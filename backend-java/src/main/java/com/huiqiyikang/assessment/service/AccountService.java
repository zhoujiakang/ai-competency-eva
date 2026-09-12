package com.huiqiyikang.assessment.service;

import com.huiqiyikang.assessment.entity.*;
import com.huiqiyikang.assessment.mapper.*;
import org.springframework.stereotype.Service;
import java.util.Collection;
import java.util.List;
import java.util.Optional;

@Service
public class AccountService {
    private final UserRepository users;
    private final StudentRepository students;
    private final TeacherRepository teachers;
    public AccountService(UserRepository users, StudentRepository students, TeacherRepository teachers) {
        this.users = users; this.students = students; this.teachers = teachers;
    }
    public Optional<User> findById(Long id) { return users.findById(id); }
    /** 批量取用户，供列表接口一次装配学生名/账号，避免逐条查询。 */
    public List<User> findAllById(Collection<Long> ids) { return users.findAllById(ids); }
    public Optional<User> findByUsername(String username) { return users.findByUsername(username); }
    public boolean existsByUsername(String username) { return users.existsByUsername(username); }
    public User save(User user) { return users.save(user); }
    public Student save(Student student) { students.save(student); return student; }
    public Teacher save(Teacher teacher) { teachers.save(teacher); return teacher; }
    public boolean existsStudent(Long id) { return students.existsByUserId(id); }
    public boolean existsTeacher(Long id) { return teachers.existsByUserId(id); }
    public boolean existsByUserId(Long id) { return users.findById(id).isPresent(); }
}
