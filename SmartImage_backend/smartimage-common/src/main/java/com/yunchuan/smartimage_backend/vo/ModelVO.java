package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class ModelVO {
    private String h5Url;
    private String modelPath;
    private String modelUrl;
    private String volumeUrl;
    private String labelUrl;
    private String heatmapPath;
    private String heatmapUrl;
    private String oarPath;
    private String oarUrl;
}
