package com.huiqiyikang.assessment.mapper;
import com.huiqiyikang.assessment.entity.User;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper; import java.util.Optional;
public interface UserRepository extends BaseMapperX<User>{default Optional<User> findByUsername(String username){return Optional.ofNullable(selectOne(new QueryWrapper<User>().eq("username",username)));} default boolean existsByUsername(String username){return selectCount(new QueryWrapper<User>().eq("username",username))>0;}}
