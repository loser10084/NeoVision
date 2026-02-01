package com.yunchuan.smartimage_backend.mapper;

import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ContourResultMapper {

    @Delete("delete from contour_result where study_id=#{studyId}")
    int deleteByStudyId(Long studyId);
}
