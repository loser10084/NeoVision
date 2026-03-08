package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.ConsultationSession;
import com.yunchuan.smartimage_backend.vo.ConsultationVO;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface ConsultationSessionMapper {

    @Insert("insert into consultation_session(title,patient_id,creator_id,status,materials_oss_path,created_at,updated_at) " +
            "values(#{title},#{patientId},#{creatorId},#{status},#{materialsOssPath},now(),now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ConsultationSession session);

    @Select("select * from consultation_session where id=#{id}")
    ConsultationSession findById(Long id);

    @Update("update consultation_session set updated_at=now() where id=#{id}")
    int touch(Long id);

    @Select("select s.id,s.title,s.patient_id,s.creator_id,s.status,s.materials_oss_path," +
            "coalesce(lm.text_content, concat('[', lm.message_type, '] ', ifnull(lm.file_name,''))) as last_message," +
            "date_format(lm.created_at,'%Y-%m-%d %H:%i:%s') as last_message_at," +
            "date_format(s.created_at,'%Y-%m-%d %H:%i:%s') as created_at " +
            "from consultation_session s " +
            "left join consultation_message lm on lm.id=(select cm.id from consultation_message cm where cm.consultation_id=s.id order by cm.id desc limit 1) " +
            "where s.id=#{id}")
    ConsultationVO findVOById(Long id);

    @Select("select s.id,s.title,s.patient_id,s.creator_id,s.status,s.materials_oss_path," +
            "coalesce(lm.text_content, concat('[', lm.message_type, '] ', ifnull(lm.file_name,''))) as last_message," +
            "date_format(lm.created_at,'%Y-%m-%d %H:%i:%s') as last_message_at," +
            "date_format(s.created_at,'%Y-%m-%d %H:%i:%s') as created_at " +
            "from consultation_session s " +
            "join consultation_member m on m.consultation_id=s.id and m.doctor_id=#{doctorId} " +
            "left join consultation_message lm on lm.id=(select cm.id from consultation_message cm where cm.consultation_id=s.id order by cm.id desc limit 1) " +
            "order by coalesce(lm.created_at, s.updated_at) desc")
    List<ConsultationVO> listByDoctor(Long doctorId);
}

