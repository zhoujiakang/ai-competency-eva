package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.AssessmentMessage;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper; import java.util.*;
public interface AssessmentMessageRepository extends BaseMapperX<AssessmentMessage>{default List<AssessmentMessage> findByAssessmentQuestionIdOrderBySequenceNo(Long id){return selectList(new QueryWrapper<AssessmentMessage>().eq("assessment_question_id",id).orderByAsc("sequence_no"));} default List<AssessmentMessage> findByAssessmentIdOrderByCreatedAt(Long id){return selectList(new QueryWrapper<AssessmentMessage>().eq("assessment_id",id).orderByAsc("created_at").orderByAsc("id"));}}
