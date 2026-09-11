package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.AssessmentAnswer;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper; import java.util.*;
public interface AssessmentAnswerRepository extends BaseMapperX<AssessmentAnswer>{
 default Optional<AssessmentAnswer> findByAssessmentQuestionId(Long id){return Optional.ofNullable(selectOne(new QueryWrapper<AssessmentAnswer>().eq("assessment_question_id",id)));}
 // An empty collection would render as "IN ()", which MySQL rejects; callers treat "no ids" as "no answers".
 default List<AssessmentAnswer> findByAssessmentQuestionIdIn(Collection<Long> ids){return ids==null||ids.isEmpty()?List.of():selectList(new QueryWrapper<AssessmentAnswer>().in("assessment_question_id",ids));}}
