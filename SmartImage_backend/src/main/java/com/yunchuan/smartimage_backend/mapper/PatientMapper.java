package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.Patient;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface PatientMapper {

    @Select({
            "<script>",
            "select * from patient",
            "<where>",
            "<if test='keyword!=null and keyword!=\"\"'>",
            " (name like concat('%',#{keyword},'%')",
            " or patient_no like concat('%',#{keyword},'%')",
            " or diagnosis like concat('%',#{keyword},'%')",
            " or id = #{keyword}",
            " or id in (select patient_id from patient_study where study_uid like concat('%',#{keyword},'%'))",
            " )",
            "</if>",
            "</where>",
            " order by updated_at desc",
            "</script>"
    })
    List<Patient> search(@Param("keyword") String keyword);

    @Select("select * from patient where id=#{id}")
    Patient findById(Long id);

    @Insert("insert into patient(patient_no,name,sex,age,stage,diagnosis,attending_id,created_at,updated_at) " +
            "values(#{patientNo},#{name},#{sex},#{age},#{stage},#{diagnosis},#{attendingId},now(),now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Patient patient);

    @Update({
            "<script>",
            "update patient",
            "<set>",
            "<if test='name!=null'>name=#{name},</if>",
            "<if test='sex!=null'>sex=#{sex},</if>",
            "<if test='age!=null'>age=#{age},</if>",
            "<if test='stage!=null'>stage=#{stage},</if>",
            "<if test='diagnosis!=null'>diagnosis=#{diagnosis},</if>",
            "updated_at=now()",
            "</set>",
            "where id=#{id}",
            "</script>"
    })
    int update(Patient patient);

    @Delete("delete from patient where id=#{id}")
    int delete(Long id);
}
