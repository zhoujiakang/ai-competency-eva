package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.AssessmentPointScore;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import java.util.List;
public interface AssessmentPointScoreRepository extends BaseMapperX<AssessmentPointScore>{
    default List<AssessmentPointScore> findByAssessmentId(Long assessmentId){
        return selectList(new QueryWrapper<AssessmentPointScore>().eq("assessment_id",assessmentId).orderByAsc("dimension").orderByAsc("assessment_point"));
    }
}
