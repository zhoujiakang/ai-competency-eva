package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.AssessmentQuestion;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper; import java.util.*;
public interface AssessmentQuestionRepository extends BaseMapperX<AssessmentQuestion>{default List<AssessmentQuestion> findByAssessmentIdOrderBySequenceNo(Long id){return selectList(new QueryWrapper<AssessmentQuestion>().eq("assessment_id",id).orderByAsc("sequence_no"));} default Optional<AssessmentQuestion> findByIdAndAssessmentId(Long id,Long assessmentId){return Optional.ofNullable(selectOne(new QueryWrapper<AssessmentQuestion>().eq("id",id).eq("assessment_id",assessmentId)));}
 /** 一次取多次测评的题目快照，按 assessment_id 分组交给调用方。 */
 default List<AssessmentQuestion> findByAssessmentIdIn(Collection<Long> ids){return ids==null||ids.isEmpty()?List.of():selectList(new QueryWrapper<AssessmentQuestion>().in("assessment_id",ids).orderByAsc("assessment_id").orderByAsc("sequence_no"));}}
