package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.DoctorFriend;
import com.yunchuan.smartimage_backend.entity.DoctorUser;
import com.yunchuan.smartimage_backend.vo.DoctorSimpleVO;
import org.apache.ibatis.annotations.*;

import java.util.List;

@Mapper
public interface DoctorSocialMapper {

    @Select("select * from doctor_user where id=#{id}")
    DoctorUser findById(Long id);

    @Select({
            "<script>",
            "select * from doctor_user",
            "where id != #{currentUserId}",
            "<if test='keyword != null and keyword.length() > 0'>",
            " and (name like concat('%',#{keyword},'%')",
            "  or mobile like concat('%',#{keyword},'%')",
            "  or hospital like concat('%',#{keyword},'%')",
            "  or dept like concat('%',#{keyword},'%'))",
            "</if>",
            "order by updated_at desc",
            "limit 50",
            "</script>"
    })
    List<DoctorUser> searchDoctors(@Param("currentUserId") Long currentUserId,
                                   @Param("keyword") String keyword);

    @Select("select case when doctor_id=#{doctorId} then friend_id else doctor_id end as friend_id from doctor_friend where doctor_id=#{doctorId} or friend_id=#{doctorId}")
    List<Long> listFriendIds(Long doctorId);

    @Select("select d.id,d.name,d.hospital,d.dept,d.mobile,1 as friend " +
            "from doctor_friend f " +
            "join doctor_user d on d.id = case when f.doctor_id=#{doctorId} then f.friend_id else f.doctor_id end " +
            "where f.doctor_id=#{doctorId} or f.friend_id=#{doctorId} " +
            "order by f.updated_at desc")
    List<DoctorSimpleVO> listFriends(Long doctorId);

    @Select("select count(1) from doctor_friend where doctor_id=#{doctorId} and friend_id=#{friendId}")
    int countFriendPair(@Param("doctorId") Long doctorId,
                        @Param("friendId") Long friendId);

    @Insert("insert into doctor_friend(doctor_id,friend_id,created_by,created_at,updated_at) values(#{doctorId},#{friendId},#{createdBy},now(),now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insertFriend(DoctorFriend doctorFriend);

    @Delete("delete from doctor_friend where doctor_id=#{doctorId} and friend_id=#{friendId}")
    int deleteFriend(@Param("doctorId") Long doctorId,
                     @Param("friendId") Long friendId);
}
