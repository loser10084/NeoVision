package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.ContourResult;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface ContourResultMapper {

    @Select("select * from contour_result where patient_id=#{patientId} order by updated_at desc")
    List<ContourResult> listByPatientId(Long patientId);

    @Select("select * from contour_result where id=#{id}")
    ContourResult findById(Long id);

    @Select("select * from contour_result where patient_id=#{patientId} and study_id=#{studyId} and type=#{type} order by version desc limit 1")
    ContourResult findLatest(Long patientId, Long studyId, String type);

    @Insert("insert into contour_result(patient_id,study_id,type,version,status,storage_path,confidence_map,created_by,created_at,updated_at) " +
            "values(#{patientId},#{studyId},#{type},#{version},#{status},#{storagePath},#{confidenceMap},#{createdBy},now(),now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ContourResult contour);

    @Update({
            "<script>",
            "update contour_result",
            "<set>",
            "<if test='status!=null'>status=#{status},</if>",
            "<if test='storagePath!=null'>storage_path=#{storagePath},</if>",
            "<if test='confidenceMap!=null'>confidence_map=#{confidenceMap},</if>",
            "<if test='version!=null'>version=#{version},</if>",
            "<if test='createdBy!=null'>created_by=#{createdBy},</if>",
            "updated_at=now()",
            "</set>",
            "where id=#{id}",
            "</script>"
    })
    int update(ContourResult contour);

    @Delete("delete from contour_result where patient_id=#{patientId}")
    int deleteByPatientId(Long patientId);
}
