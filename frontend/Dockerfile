FROM nginx:alpine

# 安装bash和gettext（用于envsubst）
RUN apk add --no-cache bash gettext

# 复制前端构建文件
COPY dist/ /usr/share/nginx/html/

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q --spider http://localhost/health || exit 1

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"] 