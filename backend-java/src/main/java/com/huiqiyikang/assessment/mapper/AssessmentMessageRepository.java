package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.AssessmentMessage;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper; import java.util.*;
public interface AssessmentMessageRepository extends BaseMapperX<AssessmentMessage>{default List<AssessmentMessage> findByAssessmentQuestionIdOrderBySequenceNo(Long id){return selectList(new QueryWrapper<AssessmentMessage>().eq("assessment_question_id",id).orderByAsc("sequence_no"));} default List<AssessmentMessage> findByAssessmentIdOrderByCreatedAt(Long id){return selectList(new QueryWrapper<AssessmentMessage>().eq("assessment_id",id).orderByAsc("created_at").orderByAsc("id"));}
 /** 一次取多道题的对话，替代"每道题查一次"。 */
 default List<AssessmentMessage> findByAssessmentQuestionIdIn(Collection<Long> ids){return ids==null||ids.isEmpty()?List.of():selectList(new QueryWrapper<AssessmentMessage>().in("assessment_question_id",ids).orderByAsc("assessment_question_id").orderByAsc("sequence_no"));}}
