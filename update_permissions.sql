-- 权限数据更新脚本
-- 根据截图中的权限列表更新数据库中的权限数据

-- 清空现有权限数据（谨慎操作，确保备份）
-- 如果只想更新而不清空，可以注释掉以下三行
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE role_permissions;
TRUNCATE TABLE permissions;
SET FOREIGN_KEY_CHECKS = 1;

-- 插入权限数据
INSERT INTO permissions (id, name, code, description, type, parent_id, path, level, sort_order, is_menu, icon, component, route_path, status) 
VALUES 
-- 系统管理
(1, '系统管理', 'system', '系统管理相关功能', 1, NULL, '1', 0, 1, 1, 'bi-gear', NULL, NULL, 1),

-- 用户管理
(2, '用户管理', 'system:user', '用户管理相关功能', 2, 1, '1/2', 1, 1, 1, 'bi-people', 'views/system/User.vue', '/system/user', 1),
(3, '查看用户', 'system:user:view', '查看用户列表', 3, 2, '1/2/3', 2, 1, 0, NULL, NULL, NULL, 1),
(4, '添加用户', 'system:user:add', '添加新用户', 3, 2, '1/2/4', 2, 2, 0, NULL, NULL, NULL, 1),
(5, '编辑用户', 'system:user:edit', '编辑用户信息', 3, 2, '1/2/5', 2, 3, 0, NULL, NULL, NULL, 1),
(6, '删除用户', 'system:user:delete', '删除用户', 3, 2, '1/2/6', 2, 4, 0, NULL, NULL, NULL, 1),
(7, '分配角色', 'system:user:assign', '为用户分配角色', 3, 2, '1/2/7', 2, 5, 0, NULL, NULL, NULL, 1),

-- 角色管理
(8, '角色管理', 'system:role', '角色管理相关功能', 2, 1, '1/8', 1, 2, 1, 'bi-person-badge', 'views/system/Role.vue', '/system/role', 1),
(9, '查看角色', 'system:role:view', '查看角色列表', 3, 8, '1/8/9', 2, 1, 0, NULL, NULL, NULL, 1),
(10, '添加角色', 'system:role:add', '添加新角色', 3, 8, '1/8/10', 2, 2, 0, NULL, NULL, NULL, 1),
(11, '编辑角色', 'system:role:edit', '编辑角色信息', 3, 8, '1/8/11', 2, 3, 0, NULL, NULL, NULL, 1),
(12, '删除角色', 'system:role:delete', '删除角色', 3, 8, '1/8/12', 2, 4, 0, NULL, NULL, NULL, 1),
(13, '分配权限', 'system:role:assign', '为角色分配权限', 3, 8, '1/8/13', 2, 5, 0, NULL, NULL, NULL, 1),

-- 权限管理
(14, '权限管理', 'system:permission', '权限管理相关功能', 2, 1, '1/14', 1, 3, 1, 'bi-shield-lock', 'views/system/Permission.vue', '/system/permission', 1),
(15, '查看权限', 'system:permission:view', '查看权限列表', 3, 14, '1/14/15', 2, 1, 0, NULL, NULL, NULL, 1),
(16, '添加权限', 'system:permission:add', '添加新权限', 3, 14, '1/14/16', 2, 2, 0, NULL, NULL, NULL, 1),
(17, '编辑权限', 'system:permission:edit', '编辑权限信息', 3, 14, '1/14/17', 2, 3, 0, NULL, NULL, NULL, 1),
(18, '删除权限', 'system:permission:delete', '删除权限', 3, 14, '1/14/18', 2, 4, 0, NULL, NULL, NULL, 1),

-- 股票管理
(19, '股票管理', 'stock', '股票管理相关功能', 1, NULL, '19', 0, 2, 1, 'bi-graph-up', NULL, NULL, 1),

-- 股票列表
(20, '股票列表', 'stock:list', '股票列表管理', 2, 19, '19/20', 1, 1, 1, 'bi-list-ul', 'views/stock/StockList.vue', '/stock/list', 1),
(21, '查看股票', 'stock:list:view', '查看股票列表', 3, 20, '19/20/21', 2, 1, 0, NULL, NULL, NULL, 1),
(22, '添加股票', 'stock:list:add', '添加新股票', 3, 20, '19/20/22', 2, 2, 0, NULL, NULL, NULL, 1),
(23, '编辑股票', 'stock:list:edit', '编辑股票信息', 3, 20, '19/20/23', 2, 3, 0, NULL, NULL, NULL, 1),
(24, '删除股票', 'stock:list:delete', '删除股票', 3, 20, '19/20/24', 2, 4, 0, NULL, NULL, NULL, 1),

-- 持仓管理
(25, '持仓管理', 'stock:holdings', '股票持仓管理', 2, 19, '19/25', 1, 2, 1, 'bi-briefcase', 'views/stock/Holdings.vue', '/stock/holdings', 1),
(26, '查看持仓', 'stock:holdings:view', '查看持仓列表', 3, 25, '19/25/26', 2, 1, 0, NULL, NULL, NULL, 1),
(27, '导出持仓', 'stock:holdings:export', '导出持仓数据', 3, 25, '19/25/27', 2, 2, 0, NULL, NULL, NULL, 1),

-- 交易管理
(28, '交易管理', 'transaction', '交易管理相关功能', 1, NULL, '28', 0, 3, 1, 'bi-currency-exchange', NULL, NULL, 1),

-- 交易记录
(29, '交易记录', 'transaction:records', '交易记录管理', 2, 28, '28/29', 1, 1, 1, 'bi-journal-text', 'views/transaction/Records.vue', '/transaction/records', 1),
(30, '查看交易', 'transaction:records:view', '查看交易记录', 3, 29, '28/29/30', 2, 1, 0, NULL, NULL, NULL, 1),
(31, '添加交易', 'transaction:records:add', '添加新交易记录', 3, 29, '28/29/31', 2, 2, 0, NULL, NULL, NULL, 1),
(32, '编辑交易', 'transaction:records:edit', '编辑交易记录', 3, 29, '28/29/32', 2, 3, 0, NULL, NULL, NULL, 1),
(33, '删除交易', 'transaction:records:delete', '删除交易记录', 3, 29, '28/29/33', 2, 4, 0, NULL, NULL, NULL, 1),
(34, '导出交易', 'transaction:records:export', '导出交易记录', 3, 29, '28/29/34', 2, 5, 0, NULL, NULL, NULL, 1),

-- 交易统计
(35, '交易统计', 'transaction:stats', '交易统计分析', 2, 28, '28/35', 1, 2, 1, 'bi-bar-chart', 'views/transaction/Stats.vue', '/transaction/stats', 1),
(36, '查看统计', 'transaction:stats:view', '查看交易统计数据', 3, 35, '28/35/36', 2, 1, 0, NULL, NULL, NULL, 1),
(37, '导出统计', 'transaction:stats:export', '导出交易统计数据', 3, 35, '28/35/37', 2, 2, 0, NULL, NULL, NULL, 1)

ON DUPLICATE KEY UPDATE 
    name = VALUES(name),
    code = VALUES(code),
    description = VALUES(description),
    type = VALUES(type),
    parent_id = VALUES(parent_id),
    path = VALUES(path),
    level = VALUES(level),
    sort_order = VALUES(sort_order),
    is_menu = VALUES(is_menu),
    icon = VALUES(icon),
    component = VALUES(component),
    route_path = VALUES(route_path),
    status = VALUES(status);

-- 重置自增ID
ALTER TABLE permissions AUTO_INCREMENT = 38;

-- 为超级管理员角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'admin'),
    id
FROM 
    permissions
ON DUPLICATE KEY UPDATE role_id = role_id;

-- 为普通用户角色分配基本权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 
    (SELECT id FROM roles WHERE code = 'user'),
    id
FROM 
    permissions
WHERE 
    code IN ('system:user:view', 'system:role:view', 'system:permission:view', 
             'stock:list:view', 'stock:holdings:view', 
             'transaction:records:view', 'transaction:stats:view')
ON DUPLICATE KEY UPDATE role_id = role_id;

-- 更新权限类型为"未知"
UPDATE permissions SET type = 3 WHERE type IS NULL OR type = 0;

-- 输出更新结果
SELECT 'Permission data updated successfully!' AS message;
SELECT COUNT(*) AS total_permissions FROM permissions;
SELECT COUNT(*) AS admin_permissions FROM role_permissions WHERE role_id = (SELECT id FROM roles WHERE code = 'admin');
SELECT COUNT(*) AS user_permissions FROM role_permissions WHERE role_id = (SELECT id FROM roles WHERE code = 'user');