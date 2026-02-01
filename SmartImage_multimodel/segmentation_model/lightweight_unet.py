"""
轻量级U-Net模型 - 用于快速生成GTV初稿（阶段1）
目标：20秒内完成分割
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    """(convolution => [BN] => ReLU) * 2"""
    
    def __init__(self, in_channels, out_channels, mid_channels=None):
        super().__init__()
        if not mid_channels:
            mid_channels = out_channels
        self.double_conv = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.double_conv(x)


class Down(nn.Module):
    """Downscaling with maxpool then double conv"""
    
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels)
        )

    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    """Upscaling then double conv"""
    
    def __init__(self, in_channels, out_channels, bilinear=True):
        super().__init__()
        
        if bilinear:
            self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=True)
            self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
        else:
            self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
            self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1, x2):
        x1 = self.up(x1)
        # 输入是 CHW
        diffY = x2.size()[2] - x1.size()[2]
        diffX = x2.size()[3] - x1.size()[3]

        x1 = F.pad(x1, [diffX // 2, diffX - diffX // 2,
                        diffY // 2, diffY - diffY // 2])
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class LightweightUNet(nn.Module):
    """
    轻量级U-Net模型
    用于快速生成GTV初稿，参数量小，推理速度快
    """
    
    def __init__(self, n_channels=1, n_classes=2, bilinear=True):
        """
        Args:
            n_channels: 输入通道数（1=单模态CT，2=多模态CT+MRI）
            n_classes: 输出类别数（2=背景+GTV）
            bilinear: 是否使用双线性上采样
        """
        super(LightweightUNet, self).__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes
        self.bilinear = bilinear

        # 编码器（下采样）- 使用较小的通道数以降低计算量
        self.inc = DoubleConv(n_channels, 32)
        self.down1 = Down(32, 64)
        self.down2 = Down(64, 128)
        self.down3 = Down(128, 256)
        
        # 瓶颈层
        factor = 2 if bilinear else 1
        self.down4 = Down(256, 512 // factor)
        
        # 解码器（上采样）
        self.up1 = Up(512, 256 // factor, bilinear)
        self.up2 = Up(256, 128 // factor, bilinear)
        self.up3 = Up(128, 64 // factor, bilinear)
        self.up4 = Up(64, 32, bilinear)
        
        # 输出层
        self.outc = nn.Conv2d(32, n_classes, kernel_size=1)
        
        # 置信度估计分支
        self.confidence_head = nn.Sequential(
            nn.Conv2d(32, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 1, kernel_size=1),
            nn.Sigmoid()
        )

    def forward(self, x):
        """
        Args:
            x: 输入图像 [B, C, H, W]
        Returns:
            logits: 分割logits [B, n_classes, H, W]
            confidence: 置信度图 [B, 1, H, W]
        """
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)
        
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)
        
        logits = self.outc(x)
        confidence = self.confidence_head(x)
        
        return logits, confidence

    def predict(self, x):
        """推理接口，返回分割结果和置信度"""
        self.eval()
        with torch.no_grad():
            logits, confidence = self.forward(x)
            probs = F.softmax(logits, dim=1)
            pred = torch.argmax(probs, dim=1)
        return pred, confidence


if __name__ == '__main__':
    # 测试模型
    model = LightweightUNet(n_channels=1, n_classes=2)
    x = torch.randn(1, 1, 256, 256)
    logits, confidence = model(x)
    print(f"输入形状: {x.shape}")
    print(f"输出logits形状: {logits.shape}")
    print(f"置信度形状: {confidence.shape}")
    print(f"模型参数量: {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M")

