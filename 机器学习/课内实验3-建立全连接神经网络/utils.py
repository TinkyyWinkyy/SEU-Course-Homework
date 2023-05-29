﻿import torch
from torch.utils.data import DataLoader
from torchvision import transforms
import torch.nn.functional as F
from d2l.torch import d2l


def to_device(data, device):
    if isinstance(data, (list, tuple)):
        return [to_device(x, device) for x in data]
    return data.to(device, non_blocking=True)


def get_default_device():
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class CudaDataLoader(DataLoader):
    def __init__(self,
                 dataset,
                 batch_size=1,
                 shuffle=False,
                 sampler=None,
                 batch_sampler=None,
                 num_workers=0,
                 collate_fn=None,
                 pin_memory=False,
                 drop_last=False,
                 timeout=0,
                 worker_init_fn=None,
                 multiprocessing_context=None):
        super(CudaDataLoader,
              self).__init__(dataset, batch_size, shuffle, sampler,
                             batch_sampler, num_workers, collate_fn,
                             pin_memory, drop_last, timeout, worker_init_fn,
                             multiprocessing_context)
        self.device = get_default_device()

    def __iter__(self):
        base_iterator = super().__iter__()
        for batch in base_iterator:
            yield to_device(batch, self.device)


train_tfms = transforms.Compose([
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ToTensor(),
    transforms.Normalize((0.1307, ), (0.3081, ))
])

test_tfms = transforms.Compose(
    [transforms.ToTensor(),
     transforms.Normalize((0.1307, ), (0.3081, ))])


def relu(x):
    return torch.max(x, torch.zeros_like(x))


def fit_and_test(model, epochs, train_dl, test_dl, train_step):
    history = []
    for epoch in range(epochs):
        if hasattr(model, 'train'):
            model.train()
        train_losses = []
        for images, labels in train_dl:
            train_losses.append(train_step(model, images, labels))
        if hasattr(model, 'eval'):
            model.eval()
        test_losses = []
        test_accs = []
        for images, labels in test_dl:
            outputs = model(images)
            test_losses.append(
                F.cross_entropy(outputs,
                                labels))
            _, preds = torch.max(outputs, dim=1)
            test_accs.append(
                torch.tensor(torch.sum(preds == labels).item() / len(preds)))

        history.append({
            'train_loss': torch.stack(train_losses).mean().item(),
            'test_loss': torch.stack(test_losses).mean().item(),
            'test_acc': torch.stack(test_accs).mean()
        })
        print(
            f"Epoch[{epoch + 1:d}]: train_loss: {history[-1]['train_loss']:.4f}, test_loss: {history[-1]['test_loss']:.4f}, test_acc: {history[-1]['test_acc']:.4f}"
        )
    return history


class Animator:  # @save
    def __init__(self,
                 xlabel=None,
                 ylabel=None,
                 legend=None,
                 xlim=None,
                 ylim=None,
                 xscale='linear',
                 yscale='linear',
                 fmts=('-', 'm--', 'g-.', 'r:'),
                 nrows=1,
                 ncols=1,
                 figsize=(3.5, 2.5)):
        # 增量地绘制多条线
        if legend is None:
            legend = []
        d2l.use_svg_display()
        self.fig, self.axes = d2l.plt.subplots(nrows, ncols, figsize=figsize)
        if nrows * ncols == 1:
            self.axes = [
                self.axes,
            ]
        # 使用lambda函数捕获参数
        self.config_axes = lambda: d2l.set_axes(self.axes[
            0], xlabel, ylabel, xlim, ylim, xscale, yscale, legend)
        self.X, self.Y, self.fmts = None, None, fmts

    def add(self, x, y):
        # 向图表中添加多个数据点
        if not hasattr(y, "__len__"):
            y = [y]
        n = len(y)
        if not hasattr(x, "__len__"):
            x = [x] * n
        if not self.X:
            self.X = [[] for _ in range(n)]
        if not self.Y:
            self.Y = [[] for _ in range(n)]
        for i, (a, b) in enumerate(zip(x, y)):
            if a is not None and b is not None:
                self.X[i].append(a)
                self.Y[i].append(b)
        self.axes[0].cla()
        for x, y, fmt in zip(self.X, self.Y, self.fmts):
            self.axes[0].plot(x, y, fmt)
        self.config_axes()
        display.display(self.fig)
        display.clear_output(wait=True)
