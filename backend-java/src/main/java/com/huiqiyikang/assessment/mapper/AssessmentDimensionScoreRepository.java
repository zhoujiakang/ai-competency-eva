package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.AssessmentDimensionScore;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import java.util.List;
public interface AssessmentDimensionScoreRepository extends BaseMapperX<AssessmentDimensionScore>{
    default List<AssessmentDimensionScore> findByAssessmentId(Long assessmentId){
        return selectList(new QueryWrapper<AssessmentDimensionScore>().eq("assessment_id",assessmentId).orderByAsc("dimension"));
    }
}
