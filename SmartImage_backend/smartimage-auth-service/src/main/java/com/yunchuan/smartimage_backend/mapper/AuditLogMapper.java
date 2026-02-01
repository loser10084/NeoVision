package com.yunchuan.smartimage_backend.mapper;

import com.yunchuan.smartimage_backend.entity.AuditLog;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;

@Mapper
public interface AuditLogMapper {

    @Insert("insert into audit_log(user_id,action,detail,created_at) values(#{userId},#{action},#{detail},now())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AuditLog log);
}
