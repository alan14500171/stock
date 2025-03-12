#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
导出数据库结构并在本地重建
"""

import os
import sys
import logging
import pymysql
from pymysql.cursors import DictCursor

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.db_config import get_db_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def export_table_structure(config, table_name):
    """导出表结构"""
    try:
        # 连接到数据库
        conn = pymysql.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            db=config['db'],
            port=config['port'],
            charset=config['charset'],
            cursorclass=DictCursor
        )
        
        with conn.cursor() as cursor:
            # 获取表结构
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            # 获取表的创建语句
            cursor.execute(f"SHOW CREATE TABLE {table_name}")
            create_table = cursor.fetchone()
            
            # 获取表的前10条数据
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
            sample_data = cursor.fetchall()
            
            return {
                'columns': columns,
                'create_table': create_table['Create Table'] if 'Create Table' in create_table else None,
                'sample_data': sample_data
            }
    except Exception as e:
        logger.error(f"导出表结构失败: {str(e)}")
        return None
    finally:
        if conn:
            conn.close()

def get_all_tables(config):
    """获取所有表名"""
    try:
        # 连接到数据库
        conn = pymysql.connect(
            host=config['host'],
            user=config['user'],
            password=config['password'],
            db=config['db'],
            port=config['port'],
            charset=config['charset'],
            cursorclass=DictCursor
        )
        
        with conn.cursor() as cursor:
            # 获取所有表名
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            # 提取表名
            table_names = [list(table.values())[0] for table in tables]
            
            return table_names
    except Exception as e:
        logger.error(f"获取表名失败: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def generate_create_script(structures):
    """生成创建脚本"""
    script = "-- 数据库结构创建脚本\n\n"
    
    # 添加创建数据库语句
    script += "CREATE DATABASE IF NOT EXISTS `stock` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n\n"
    script += "USE `stock`;\n\n"
    
    # 添加创建表语句
    for table_name, structure in structures.items():
        if structure and structure['create_table']:
            script += f"-- 表结构: {table_name}\n"
            script += f"{structure['create_table']};\n\n"
    
    return script

def generate_sample_data_script(structures):
    """生成样本数据插入脚本"""
    script = "-- 样本数据插入脚本\n\n"
    
    # 添加USE语句
    script += "USE `stock`;\n\n"
    
    # 添加插入语句
    for table_name, structure in structures.items():
        if structure and structure['sample_data'] and len(structure['sample_data']) > 0:
            script += f"-- 表数据: {table_name}\n"
            
            # 获取列名
            columns = [col['Field'] for col in structure['columns']]
            columns_str = ", ".join([f"`{col}`" for col in columns])
            
            # 生成INSERT语句
            script += f"INSERT INTO `{table_name}` ({columns_str}) VALUES\n"
            
            # 生成VALUES部分
            values_list = []
            for row in structure['sample_data']:
                values = []
                for col in columns:
                    if col in row and row[col] is not None:
                        if isinstance(row[col], str):
                            # 转义字符串中的单引号
                            escaped_value = row[col].replace("'", "''")
                            values.append(f"'{escaped_value}'")
                        else:
                            values.append(f"'{row[col]}'")
                    else:
                        values.append("NULL")
                values_list.append(f"({', '.join(values)})")
            
            script += ",\n".join(values_list) + ";\n\n"
    
    return script

def generate_markdown_doc(structures):
    """生成Markdown文档"""
    doc = "# 数据库结构文档\n\n"
    
    for table_name, structure in structures.items():
        if structure:
            doc += f"## 表: {table_name}\n\n"
            
            # 添加表结构
            doc += "### 表结构\n\n"
            doc += "| 字段名 | 类型 | 可空 | 键 | 默认值 | 额外 |\n"
            doc += "|--------|------|------|-----|--------|------|\n"
            
            for col in structure['columns']:
                doc += f"| {col['Field']} | {col['Type']} | {col['Null']} | {col['Key']} | {col['Default'] if col['Default'] else 'NULL'} | {col['Extra']} |\n"
            
            doc += "\n"
            
            # 添加样本数据
            if structure['sample_data'] and len(structure['sample_data']) > 0:
                doc += "### 样本数据\n\n"
                
                # 获取列名
                columns = [col['Field'] for col in structure['columns']]
                
                # 表头
                doc += "| " + " | ".join(columns) + " |\n"
                doc += "|" + "|".join(["---" for _ in columns]) + "|\n"
                
                # 数据行
                for row in structure['sample_data']:
                    row_values = []
                    for col in columns:
                        if col in row and row[col] is not None:
                            row_values.append(str(row[col]).replace("|", "\\|"))
                        else:
                            row_values.append("NULL")
                    doc += "| " + " | ".join(row_values) + " |\n"
                
                doc += "\n"
    
    return doc

def main():
    """主函数"""
    try:
        # 获取数据库配置
        config = get_db_config()
        
        # 获取所有表名
        table_names = get_all_tables(config)
        
        if not table_names:
            logger.error("未找到任何表")
            return
        
        logger.info(f"找到 {len(table_names)} 个表: {', '.join(table_names)}")
        
        # 导出表结构
        structures = {}
        for table_name in table_names:
            logger.info(f"导出表结构: {table_name}")
            structure = export_table_structure(config, table_name)
            structures[table_name] = structure
        
        # 生成创建脚本
        create_script = generate_create_script(structures)
        with open("db_structure.sql", "w") as f:
            f.write(create_script)
        logger.info("创建脚本已保存到 db_structure.sql")
        
        # 生成样本数据脚本
        sample_data_script = generate_sample_data_script(structures)
        with open("db_sample_data.sql", "w") as f:
            f.write(sample_data_script)
        logger.info("样本数据脚本已保存到 db_sample_data.sql")
        
        # 生成Markdown文档
        markdown_doc = generate_markdown_doc(structures)
        with open("db_structure.md", "w") as f:
            f.write(markdown_doc)
        logger.info("Markdown文档已保存到 db_structure.md")
        
        # 打印transaction_splits表的结构
        if 'transaction_splits' in structures and structures['transaction_splits']:
            print("\n交易分单表(transaction_splits)结构:")
            for col in structures['transaction_splits']['columns']:
                print(f"- {col['Field']}: {col['Type']} ({col['Null']})")
        
    except Exception as e:
        logger.error(f"导出数据库结构失败: {str(e)}")

if __name__ == "__main__":
    main() 