package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.ConsultationMessage;
import com.yunchuan.smartimage_backend.vo.ConsultationMessageVO;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface ConsultationMessageMapper {

    @Insert("insert into consultation_message(consultation_id,sender_id,message_type,text_content,oss_path,file_name,file_size,mime_type,created_at) " +
            "values(#{consultationId},#{senderId},#{messageType},#{textContent},#{ossPath},#{fileName},#{fileSize},#{mimeType},now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(ConsultationMessage message);

    @Select("select m.id,m.consultation_id,m.sender_id,d.name as sender_name,m.message_type,m.text_content,m.oss_path,m.file_name,m.file_size,m.mime_type," +
            "date_format(m.created_at,'%Y-%m-%d %H:%i:%s') as created_at " +
            "from consultation_message m " +
            "join doctor_user d on d.id=m.sender_id " +
            "where m.id=#{id}")
    ConsultationMessageVO findVOById(Long id);

    @Select({
            "<script>",
            "select m.id,m.consultation_id,m.sender_id,d.name as sender_name,m.message_type,m.text_content,m.oss_path,m.file_name,m.file_size,m.mime_type,",
            "date_format(m.created_at,'%Y-%m-%d %H:%i:%s') as created_at",
            "from consultation_message m",
            "join doctor_user d on d.id=m.sender_id",
            "where m.consultation_id=#{consultationId}",
            "<if test='beforeId!=null'> and m.id &lt; #{beforeId}</if>",
            "order by m.id desc",
            "limit #{limit}",
            "</script>"
    })
    List<ConsultationMessageVO> listMessages(@Param("consultationId") Long consultationId,
                                             @Param("beforeId") Long beforeId,
                                             @Param("limit") int limit);
}
