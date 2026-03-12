package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class StudyArtifactsVO {
    private Long studyId;
    private HeatmapArtifact heatmap;
    private CpdmArtifact cpdm;

    @Data
    public static class HeatmapArtifact {
        private String filePath;
        private String fileType;
        private String updatedAt;
    }

    @Data
    public static class CpdmArtifact {
        private String petPngPath;
        private String fileType;
        private String updatedAt;
    }
}
