package com.yunchuan.smartimage_backend.mapper;

import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface FileUploadMapper {

    @Delete("delete from file_upload where patient_id=#{patientId}")
    int deleteByPatientId(Long patientId);
}
