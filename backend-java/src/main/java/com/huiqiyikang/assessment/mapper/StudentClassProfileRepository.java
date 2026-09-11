package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.StudentClassProfile;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import java.util.List;
import java.util.Optional;
public interface StudentClassProfileRepository extends BaseMapperX<StudentClassProfile>{
    /** 班级隔离的取数入口：这个学生在这个班级下的画像只有一行。 */
    default Optional<StudentClassProfile> findByClassIdAndStudentUserId(Long classId, Long studentUserId){
        return selectList(new QueryWrapper<StudentClassProfile>()
                .eq("class_id", classId).eq("student_user_id", studentUserId).last("LIMIT 1"))
                .stream().findFirst();
    }
    /** 教师端做班级分析时用：一次取全班的画像。 */
    default List<StudentClassProfile> findByClassId(Long classId){
        return selectList(new QueryWrapper<StudentClassProfile>().eq("class_id", classId));
    }
}
