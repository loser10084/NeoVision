package com.yunchuan.smartimage_backend.vo;

import lombok.Data;

@Data
public class PatientSummaryVO {
    private Long id;
    private String patientNo;
    private String name;
    private String sex;
    private Integer age;
    private String stage;
    private String diagnosis;
    private String studyId;
    private String status;
    private boolean gtvReady;
    private boolean ctvReady;
    private String lastUpdate;
}
