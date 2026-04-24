# 记账分摊功能

## 功能概述

记账分摊功能允许旅行成员记录支出并自动计算分摊，支持多人旅行的费用管理。

## 核心功能

### 1. 支出记录
- 记录支出金额、类别、描述、地点等信息
- 支持多种支出类别：餐饮、交通、住宿、娱乐、购物、其他
- 自动记录支付者和支付时间

### 2. 分摊管理
- 支持自定义分摊比例
- 默认按人数平均分摊
- 分摊金额总和必须等于支出金额

### 3. 结算计算
- 自动计算每个成员的净额（支付 - 分摊）
- 生成最优的结算方案
- 显示谁应该给谁多少钱

### 4. 支付状态跟踪
- 标记分摊是否已支付
- 记录支付时间

## API接口

### 创建支出记录
```
POST /trips/{trip_id}/expenses/
```

**请求体：**
```json
{
  "amount": 100,
  "category": "food",
  "description": "午餐",
  "location": "杭州西湖",
  "shares": [
    {"user_id": 1, "share_amount": 50},
    {"user_id": 2, "share_amount": 50}
  ]
}
```

### 获取支出记录
```
GET /trips/{trip_id}/expenses/
```

### 获取支出汇总
```
GET /trips/{trip_id}/expenses/summary/
```

**响应示例：**
```json
{
  "data": {
    "total_expenses": 300.0,
    "user_payments": {"2": 300.0},
    "user_shares": {"2": 150.0, "1": 150.0},
    "user_net": {"1": -150.0, "2": 150.0},
    "settlements": [
      {"from_user_id": 1, "to_user_id": 2, "amount": 150.0}
    ]
  }
}
```

### 修改分摊
```
POST /trips/{trip_id}/expenses/{expense_id}/split/
```

### 标记支付
```
POST /trips/{trip_id}/expenses/{expense_id}/shares/{share_id}/pay/
```

## 数据库设计

### Expense表
- `id`: 主键
- `trip_id`: 旅行ID（外键）
- `user_id`: 支付者ID（外键）
- `amount`: 支出金额
- `currency`: 货币（默认CNY）
- `category`: 支出类别
- `description`: 描述
- `location`: 地点
- `date`: 支出日期
- `created_at`: 创建时间
- `updated_at`: 更新时间

### ExpenseShare表
- `id`: 主键
- `expense_id`: 支出ID（外键）
- `user_id`: 分摊者ID（外键）
- `share_amount`: 分摊金额
- `is_paid`: 是否已支付
- `paid_at`: 支付时间
- `created_at`: 创建时间

## 前端页面

### 记账分摊页面 (`/trips/:tripId/expenses`)
- 支出汇总展示
- 添加支出表单
- 支出记录列表
- 分摊情况显示

### 功能特点
- 响应式设计，支持移动端
- 实时数据更新
- 直观的结算方案展示
- 支持多种支出类别

## 使用示例

1. **创建旅行**：用户创建旅行并邀请成员
2. **记录支出**：成员记录各自的支出
3. **设置分摊**：指定每个成员的分摊金额
4. **查看汇总**：系统自动计算结算方案
5. **标记支付**：记录分摊的支付状态

## 结算算法

使用贪心算法计算最优结算方案：
1. 计算每个成员的净额（支付 - 分摊）
2. 将成员分为净收入者和净支出者
3. 优先用净收入者的收入抵消净支出者的支出
4. 生成最终的转账方案

## 权限控制

- 只有旅行成员可以查看和操作支出记录
- 所有操作都需要有效的JWT token
- 支持角色基础的权限控制（未来扩展）

