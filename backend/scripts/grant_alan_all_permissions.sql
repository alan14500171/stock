-- 为用户alan（ID为3）添加所有权限的SQL脚本

-- 确保超级管理员角色存在
INSERT INTO stock.roles (name, description) 
VALUES ('超级管理员', '系统超级管理员，拥有所有权限')
ON DUPLICATE KEY UPDATE name=name;

-- 获取超级管理员角色ID
SET @admin_role_id = (SELECT id FROM stock.roles WHERE name = '超级管理员');

-- 将alan用户添加到超级管理员角色
INSERT INTO stock.user_roles (user_id, role_id)
VALUES (3, @admin_role_id)
ON DUPLICATE KEY UPDATE user_id=user_id;

-- 确保超级管理员角色拥有所有权限
INSERT INTO stock.role_permissions (role_id, permission_id)
SELECT 
    @admin_role_id,
    id
FROM 
    stock.permissions
ON DUPLICATE KEY UPDATE role_id=role_id;

-- 查询确认alan用户的角色
SELECT u.username, r.name as role_name
FROM stock.users u
JOIN stock.user_roles ur ON u.id = ur.user_id
JOIN stock.roles r ON ur.role_id = r.id
WHERE u.id = 3;

-- 查询确认alan用户的权限数量
SELECT u.username, COUNT(DISTINCT p.id) as permission_count
FROM stock.users u
JOIN stock.user_roles ur ON u.id = ur.user_id
JOIN stock.roles r ON ur.role_id = r.id
JOIN stock.role_permissions rp ON r.id = rp.role_id
JOIN stock.permissions p ON rp.permission_id = p.id
WHERE u.id = 3
GROUP BY u.username;

-- 查询alan用户的权限列表（可选，结果可能较长）
-- SELECT u.username, p.name as permission_name, p.code as permission_code
-- FROM stock.users u
-- JOIN stock.user_roles ur ON u.id = ur.user_id
-- JOIN stock.roles r ON ur.role_id = r.id
-- JOIN stock.role_permissions rp ON r.id = rp.role_id
-- JOIN stock.permissions p ON rp.permission_id = p.id
-- WHERE u.id = 3
-- ORDER BY p.code; 