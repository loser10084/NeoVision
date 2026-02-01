"""
nnU-Net精细修正模块（阶段4，可选）
使用nnU-Net进行高精度分割修正
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock(nn.Module):
    """标准卷积块"""
    
    def __init__(self, in_channels, out_channels, kernel_size=3, stride=1, padding=1):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding),
            nn.InstanceNorm2d(out_channels),
            nn.LeakyReLU(0.01, inplace=True)
        )
    
    def forward(self, x):
        return self.conv(x)


class NNUNetRefinement(nn.Module):
    """
    nnU-Net风格的精细修正网络
    用于对初稿进行高精度修正
    """
    
    def __init__(self, in_channels=3, n_classes=2):
        """
        Args:
            in_channels: 输入通道数（1=原图, 1=初稿掩码, 1=置信度图）
            n_classes: 输出类别数
        """
        super(NNUNetRefinement, self).__init__()
        
        # 编码器
        self.enc1 = nn.Sequential(
            ConvBlock(in_channels, 32),
            ConvBlock(32, 32)
        )
        self.enc2 = nn.Sequential(
            ConvBlock(32, 64),
            ConvBlock(64, 64)
        )
        self.enc3 = nn.Sequential(
            ConvBlock(64, 128),
            ConvBlock(128, 128)
        )
        self.enc4 = nn.Sequential(
            ConvBlock(128, 256),
            ConvBlock(256, 256)
        )
        self.enc5 = nn.Sequential(
            ConvBlock(256, 320),
            ConvBlock(320, 320)
        )
        
        # 解码器
        self.dec5 = nn.Sequential(
            ConvBlock(320 + 256, 256),
            ConvBlock(256, 256)
        )
        self.dec4 = nn.Sequential(
            ConvBlock(256 + 128, 128),
            ConvBlock(128, 128)
        )
        self.dec3 = nn.Sequential(
            ConvBlock(128 + 64, 64),
            ConvBlock(64, 64)
        )
        self.dec2 = nn.Sequential(
            ConvBlock(64 + 32, 32),
            ConvBlock(32, 32)
        )
        
        # 输出层
        self.final = nn.Conv2d(32, n_classes, kernel_size=1)
        
        # 深度监督（可选）
        self.deep_supervision = True
        if self.deep_supervision:
            self.ds5 = nn.Conv2d(256, n_classes, kernel_size=1)
            self.ds4 = nn.Conv2d(128, n_classes, kernel_size=1)
            self.ds3 = nn.Conv2d(64, n_classes, kernel_size=1)
            self.ds2 = nn.Conv2d(32, n_classes, kernel_size=1)
    
    def forward(self, x, return_ds=False):
        """
        Args:
            x: 输入 [B, C, H, W] (原图 + 初稿掩码 + 置信度)
            return_ds: 是否返回深度监督输出
        
        Returns:
            logits: 分割logits [B, n_classes, H, W]
            ds_outputs: 深度监督输出列表（如果return_ds=True）
        """
        # 编码
        e1 = self.enc1(x)
        e2 = self.enc2(F.max_pool2d(e1, 2))
        e3 = self.enc3(F.max_pool2d(e2, 2))
        e4 = self.enc4(F.max_pool2d(e3, 2))
        e5 = self.enc5(F.max_pool2d(e4, 2))
        
        # 解码
        d5 = self.dec5(torch.cat([
            F.interpolate(e5, size=e4.shape[2:], mode='bilinear', align_corners=True),
            e4
        ], dim=1))
        
        d4 = self.dec4(torch.cat([
            F.interpolate(d5, size=e3.shape[2:], mode='bilinear', align_corners=True),
            e3
        ], dim=1))
        
        d3 = self.dec3(torch.cat([
            F.interpolate(d4, size=e2.shape[2:], mode='bilinear', align_corners=True),
            e2
        ], dim=1))
        
        d2 = self.dec2(torch.cat([
            F.interpolate(d3, size=e1.shape[2:], mode='bilinear', align_corners=True),
            e1
        ], dim=1))
        
        # 最终输出
        final = self.final(d2)
        
        if return_ds and self.deep_supervision:
            ds5 = self.ds5(d5)
            ds4 = self.ds4(d4)
            ds3 = self.ds3(d3)
            ds2 = self.ds2(d2)
            
            # 上采样到原始尺寸
            ds5 = F.interpolate(ds5, size=x.shape[2:], mode='bilinear', align_corners=True)
            ds4 = F.interpolate(ds4, size=x.shape[2:], mode='bilinear', align_corners=True)
            ds3 = F.interpolate(ds3, size=x.shape[2:], mode='bilinear', align_corners=True)
            ds2 = F.interpolate(ds2, size=x.shape[2:], mode='bilinear', align_corners=True)
            
            return final, [ds2, ds3, ds4, ds5]
        
        return final
    
    def predict(self, image, initial_mask, confidence_map):
        """
        推理接口
        
        Args:
            image: 原始图像 [B, 1, H, W]
            initial_mask: 初稿掩码 [B, 1, H, W]
            confidence_map: 置信度图 [B, 1, H, W]
        
        Returns:
            refined_mask: 修正后的掩码 [B, H, W]
        """
        self.eval()
        
        # 拼接输入
        x = torch.cat([image, initial_mask, confidence_map], dim=1)
        
        with torch.no_grad():
            logits = self.forward(x)
            probs = F.softmax(logits, dim=1)
            pred = torch.argmax(probs, dim=1)
        
        return pred


if __name__ == '__main__':
    # 测试模型
    model = NNUNetRefinement(in_channels=3, n_classes=2)
    image = torch.randn(1, 1, 256, 256)
    mask = torch.randn(1, 1, 256, 256)
    conf = torch.randn(1, 1, 256, 256)
    
    logits = model.predict(image, mask, conf)
    print(f"输入图像形状: {image.shape}")
    print(f"输出形状: {logits.shape}")
    print(f"模型参数量: {sum(p.numel() for p in model.parameters()) / 1e6:.2f}M")

