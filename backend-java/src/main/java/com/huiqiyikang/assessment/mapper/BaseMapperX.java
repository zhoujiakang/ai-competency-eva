package com.huiqiyikang.assessment.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import java.util.Collection;
import java.util.List;
import java.util.Optional;

/** 项目统一的 MyBatis-Plus 基础 Mapper，屏蔽持久化 API 细节。 */
public interface BaseMapperX<T> extends BaseMapper<T> {
    default Optional<T> findById(Long id) { return Optional.ofNullable(selectById(id)); }
    default List<T> findAll() { return selectList(null); }
    /** 按 id 批量取，用于消除"列表里每条再查一次"的 N+1；空集合直接返回空列表。 */
    default List<T> findAllById(Collection<Long> ids) {
        return ids == null || ids.isEmpty() ? List.of() : selectBatchIds(ids);
    }
    default T save(T entity) {
        if (entity == null) return null;
        try {
            var id = entity.getClass().getDeclaredField("id");
            id.setAccessible(true);
            if (id.get(entity) == null) insert(entity); else updateById(entity);
        } catch (ReflectiveOperationException e) { throw new IllegalStateException("实体必须包含 id 字段", e); }
        return entity;
    }
}
