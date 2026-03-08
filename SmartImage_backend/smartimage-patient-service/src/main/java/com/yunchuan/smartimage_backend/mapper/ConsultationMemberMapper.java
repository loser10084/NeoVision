package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.ConsultationMember;
import com.yunchuan.smartimage_backend.vo.ConsultationMemberVO;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface ConsultationMemberMapper {

    @Insert("insert into consultation_member(consultation_id,doctor_id,role,joined_at) values(#{consultationId},#{doctorId},#{role},now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ConsultationMember member);

    @Select("select count(1) from consultation_member where consultation_id=#{consultationId} and doctor_id=#{doctorId}")
    int countMember(@Param("consultationId") Long consultationId,
                    @Param("doctorId") Long doctorId);

    @Delete("delete from consultation_member where consultation_id=#{consultationId} and doctor_id=#{doctorId}")
    int deleteMember(@Param("consultationId") Long consultationId,
                     @Param("doctorId") Long doctorId);

    @Select("select m.doctor_id,d.name,d.hospital,d.dept,d.mobile,m.role," +
            "date_format(m.joined_at,'%Y-%m-%d %H:%i:%s') as joined_at " +
            "from consultation_member m " +
            "join doctor_user d on d.id=m.doctor_id " +
            "where m.consultation_id=#{consultationId} " +
            "order by case when m.role='OWNER' then 0 else 1 end, m.joined_at asc")
    List<ConsultationMemberVO> listMembers(Long consultationId);
}
