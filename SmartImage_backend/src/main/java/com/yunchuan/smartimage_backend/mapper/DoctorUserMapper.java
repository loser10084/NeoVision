package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.DoctorUser;
import org.apache.ibatis.annotations.*;

@Mapper
public interface DoctorUserMapper {

    @Select("select * from doctor_user where mobile=#{mobile} limit 1")
    DoctorUser findByMobile(String mobile);

    @Select("select * from doctor_user where id=#{id}")
    DoctorUser findById(Long id);

    @Insert("insert into doctor_user(name,hospital,dept,mobile,password_hash,status,created_at,updated_at) " +
            "values(#{name},#{hospital},#{dept},#{mobile},#{passwordHash},#{status},now(),now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DoctorUser user);
}
