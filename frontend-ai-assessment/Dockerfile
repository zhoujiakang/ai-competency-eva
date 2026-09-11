# 第一阶段：把 React 打包成静态文件
FROM node:20-alpine AS build
WORKDIR /build

# 先只拷依赖清单，依赖不变时这一层可以复用缓存
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# 前端默认请求同源的 /api，由 nginx 反向代理到后端容器；
# 想直连后端域名，构建时用 --build-arg VITE_API_BASE=https://api.xxx.com/api
ARG VITE_API_BASE=/api
ENV VITE_API_BASE=$VITE_API_BASE
RUN npm run build

# 第二阶段：nginx 只负责发静态文件 + 反代 /api
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /build/dist /usr/share/nginx/html
EXPOSE 80
