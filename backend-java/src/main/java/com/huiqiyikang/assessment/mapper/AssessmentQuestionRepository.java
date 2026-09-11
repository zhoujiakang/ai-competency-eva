package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.AssessmentQuestion;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper; import java.util.*;
public interface AssessmentQuestionRepository extends BaseMapperX<AssessmentQuestion>{default List<AssessmentQuestion> findByAssessmentIdOrderBySequenceNo(Long id){return selectList(new QueryWrapper<AssessmentQuestion>().eq("assessment_id",id).orderByAsc("sequence_no"));} default Optional<AssessmentQuestion> findByIdAndAssessmentId(Long id,Long assessmentId){return Optional.ofNullable(selectOne(new QueryWrapper<AssessmentQuestion>().eq("id",id).eq("assessment_id",assessmentId)));}}
