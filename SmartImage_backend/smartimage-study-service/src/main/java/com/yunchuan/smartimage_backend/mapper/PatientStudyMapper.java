package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.PatientStudy;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface PatientStudyMapper {

    @Select("select * from patient_study where patient_id=#{patientId} order by updated_at desc")
    List<PatientStudy> listByPatientId(Long patientId);

    @Select("select * from patient_study where id=#{id}")
    PatientStudy findById(Long id);

    @Insert("insert into patient_study(patient_id,study_uid,modality,description,status,acquired_at,created_at,updated_at) " +
            "values(#{patientId},#{studyUid},#{modality},#{description},#{status},#{acquiredAt},now(),now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(PatientStudy study);

    @Update({
            "<script>",
            "update patient_study",
            "<set>",
            "<if test='studyUid!=null'>study_uid=#{studyUid},</if>",
            "<if test='modality!=null'>modality=#{modality},</if>",
            "<if test='description!=null'>description=#{description},</if>",
            "<if test='status!=null'>status=#{status},</if>",
            "updated_at=now()",
            "</set>",
            "where id=#{id}",
            "</script>"
    })
    int update(PatientStudy study);

    @Delete("delete from patient_study where id=#{id}")
    int deleteById(Long id);
}
