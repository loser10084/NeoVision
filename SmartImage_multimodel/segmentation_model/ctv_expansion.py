"""
CTV外扩模块 - 基于规则和学习型的外扩（阶段3）
结合临床规则和解剖知识，从GTV生成CTV
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from scipy import ndimage
from scipy.ndimage import distance_transform_edt, binary_dilation, binary_erosion


class RuleBasedExpansion:
    """
    基于规则的CTV外扩
    参考临床指南（如RTOG）的外扩距离
    """
    
    def __init__(self, expansion_mm=10, pixel_spacing_mm=1.0):
        """
        Args:
            expansion_mm: 外扩距离（毫米），默认10mm
            pixel_spacing_mm: 像素间距（毫米/像素）
        """
        self.expansion_mm = expansion_mm
        self.pixel_spacing_mm = pixel_spacing_mm
        self.expansion_pixels = int(expansion_mm / pixel_spacing_mm)
    
    def expand(self, gtv_mask, anatomical_mask=None):
        """
        基于规则的外扩
        
        Args:
            gtv_mask: GTV二值掩码 [H, W] 或 [D, H, W]
            anatomical_mask: 解剖结构掩码（如淋巴结区域），用于约束外扩范围
        
        Returns:
            ctv_mask: CTV二值掩码
        """
        if len(gtv_mask.shape) == 2:
            # 2D情况
            ctv_mask = binary_dilation(
                gtv_mask, 
                structure=self._get_dilation_structure(),
                iterations=self.expansion_pixels
            )
        else:
            # 3D情况
            ctv_mask = binary_dilation(
                gtv_mask,
                structure=self._get_dilation_structure_3d(),
                iterations=self.expansion_pixels
            )
        
        # 如果有解剖约束，限制外扩范围
        if anatomical_mask is not None:
            ctv_mask = ctv_mask & anatomical_mask
        
        return ctv_mask.astype(np.uint8)
    
    def _get_dilation_structure(self):
        """2D膨胀结构元素（圆形）"""
        radius = self.expansion_pixels
        y, x = np.ogrid[-radius:radius+1, -radius:radius+1]
        mask = x*x + y*y <= radius*radius
        return mask.astype(int)
    
    def _get_dilation_structure_3d(self):
        """3D膨胀结构元素（球形）"""
        radius = self.expansion_pixels
        z, y, x = np.ogrid[-radius:radius+1, -radius:radius+1, -radius:radius+1]
        mask = x*x + y*y + z*z <= radius*radius
        return mask.astype(int)


class LearningBasedExpansion(nn.Module):
    """
    学习型CTV外扩网络
    学习从GTV到CTV的映射关系，考虑解剖结构和肿瘤特征
    """
    
    def __init__(self, in_channels=2, out_channels=1):
        """
        Args:
            in_channels: 输入通道数（1=GTV, 1=解剖结构）
            out_channels: 输出通道数（1=CTV）
        """
        super(LearningBasedExpansion, self).__init__()
        
        # 编码器
        self.enc1 = self._conv_block(in_channels, 32)
        self.enc2 = self._conv_block(32, 64)
        self.enc3 = self._conv_block(64, 128)
        self.enc4 = self._conv_block(128, 256)
        
        # 瓶颈层
        self.bottleneck = self._conv_block(256, 512)
        
        # 解码器
        self.dec4 = self._conv_block(512 + 256, 256)
        self.dec3 = self._conv_block(256 + 128, 128)
        self.dec2 = self._conv_block(128 + 64, 64)
        self.dec1 = self._conv_block(64 + 32, 32)
        
        # 输出层
        self.final = nn.Conv2d(32, out_channels, kernel_size=1)
        self.sigmoid = nn.Sigmoid()
        
        # 距离变换特征
        self.distance_conv = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, 16, kernel_size=3, padding=1),
            nn.ReLU(inplace=True)
        )
    
    def _conv_block(self, in_channels, out_channels):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def forward(self, gtv_mask, anatomical_mask=None):
        """
        Args:
            gtv_mask: GTV掩码 [B, 1, H, W]
            anatomical_mask: 解剖结构掩码 [B, 1, H, W]（可选）
        
        Returns:
            ctv_logits: CTV预测logits [B, 1, H, W]
        """
        # 计算距离变换（距离GTV边界的距离）
        distance_map = self._compute_distance_map(gtv_mask)
        distance_feat = self.distance_conv(distance_map)
        
        # 拼接输入
        if anatomical_mask is not None:
            x = torch.cat([gtv_mask, anatomical_mask], dim=1)
        else:
            x = gtv_mask
        
        # 编码
        e1 = self.enc1(x)
        e2 = self.enc2(F.max_pool2d(e1, 2))
        e3 = self.enc3(F.max_pool2d(e2, 2))
        e4 = self.enc4(F.max_pool2d(e3, 2))
        
        # 瓶颈
        b = self.bottleneck(F.max_pool2d(e4, 2))
        
        # 解码
        d4 = self.dec4(torch.cat([F.interpolate(b, size=e4.shape[2:], mode='bilinear', align_corners=True), e4], dim=1))
        d3 = self.dec3(torch.cat([F.interpolate(d4, size=e3.shape[2:], mode='bilinear', align_corners=True), e3], dim=1))
        d2 = self.dec2(torch.cat([F.interpolate(d3, size=e2.shape[2:], mode='bilinear', align_corners=True), e2], dim=1))
        d1 = self.dec1(torch.cat([F.interpolate(d2, size=e1.shape[2:], mode='bilinear', align_corners=True), e1], dim=1))
        
        # 融合距离特征
        d1 = d1 + distance_feat
        
        # 输出
        out = self.final(d1)
        return self.sigmoid(out)
    
    def _compute_distance_map(self, mask):
        """计算距离变换图"""
        batch_size = mask.shape[0]
        distance_maps = []
        
        for i in range(batch_size):
            m = mask[i, 0].cpu().numpy()
            # 计算到边界的距离
            dist = distance_transform_edt(m)
            # 归一化
            if dist.max() > 0:
                dist = dist / dist.max()
            distance_maps.append(torch.from_numpy(dist).float())
        
        return torch.stack(distance_maps, dim=0).unsqueeze(1).to(mask.device)


class CTVExpansionModule:
    """
    CTV外扩模块 - 结合规则和学习型方法
    """
    
    def __init__(self, use_learning=True, expansion_mm=10, pixel_spacing_mm=1.0):
        """
        Args:
            use_learning: 是否使用学习型外扩
            expansion_mm: 规则外扩距离（毫米）
            pixel_spacing_mm: 像素间距
        """
        self.rule_expander = RuleBasedExpansion(expansion_mm, pixel_spacing_mm)
        self.use_learning = use_learning
        
        if use_learning:
            self.learning_expander = LearningBasedExpansion()
        else:
            self.learning_expander = None
    
    def expand(self, gtv_mask, anatomical_mask=None, model=None):
        """
        执行CTV外扩
        
        Args:
            gtv_mask: GTV掩码（numpy数组或torch tensor）
            anatomical_mask: 解剖结构掩码（可选）
            model: 学习型模型（如果使用）
        
        Returns:
            ctv_mask: CTV掩码
        """
        # 规则外扩
        if isinstance(gtv_mask, torch.Tensor):
            gtv_np = gtv_mask.cpu().numpy()
        else:
            gtv_np = gtv_mask
        
        rule_ctv = self.rule_expander.expand(gtv_np, anatomical_mask)
        
        # 如果使用学习型，进行修正
        if self.use_learning and model is not None:
            if isinstance(gtv_mask, torch.Tensor):
                gtv_tensor = gtv_mask
            else:
                gtv_tensor = torch.from_numpy(gtv_mask).float().unsqueeze(0).unsqueeze(0)
            
            if anatomical_mask is not None:
                if isinstance(anatomical_mask, torch.Tensor):
                    anat_tensor = anatomical_mask
                else:
                    anat_tensor = torch.from_numpy(anatomical_mask).float().unsqueeze(0).unsqueeze(0)
            else:
                anat_tensor = None
            
            model.eval()
            with torch.no_grad():
                learned_ctv = model(gtv_tensor, anat_tensor)
                learned_ctv = (learned_ctv > 0.5).float().squeeze().cpu().numpy()
            
            # 融合规则和学习型结果
            ctv_mask = np.logical_or(rule_ctv, learned_ctv).astype(np.uint8)
        else:
            ctv_mask = rule_ctv
        
        return ctv_mask


if __name__ == '__main__':
    # 测试规则外扩
    rule_expander = RuleBasedExpansion(expansion_mm=10, pixel_spacing_mm=1.0)
    gtv = np.zeros((256, 256), dtype=np.uint8)
    gtv[100:150, 100:150] = 1
    ctv = rule_expander.expand(gtv)
    print(f"GTV大小: {gtv.sum()}, CTV大小: {ctv.sum()}")
    
    # 测试学习型外扩
    model = LearningBasedExpansion()
    gtv_tensor = torch.randn(1, 1, 256, 256)
    ctv_pred = model(gtv_tensor)
    print(f"学习型输出形状: {ctv_pred.shape}")

