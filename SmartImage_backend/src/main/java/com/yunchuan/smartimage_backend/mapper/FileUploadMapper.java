package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.FileUpload;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;

@Mapper
public interface FileUploadMapper {

    @Select("select * from file_upload where id=#{id}")
    FileUpload findById(Long id);

    @Insert("insert into file_upload(patient_id,study_id,file_type,file_path,size_bytes,uploader_id,created_at) " +
            "values(#{patientId},#{studyId},#{fileType},#{filePath},#{sizeBytes},#{uploaderId},now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(FileUpload upload);
}
