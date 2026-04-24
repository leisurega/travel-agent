def calculate_settlements(expenses_data, user_map):
    """
    计算多人费用分摊的最终结算方案
    
    参数:
    expenses_data: 列表，每个元素为字典，包含:
        - 'user_id': 支付者ID
        - 'amount': 支付金额（正数）
        - 'shares': 参与本次分摊的人员列表，每个元素包含 user_id 和 share_amount
    user_map: 字典，user_id -> username 的映射
    
    返回:
    列表，每个元素为字典，包含:
        - 'from_user_id': 付款人ID
        - 'to_user_id': 收款人ID
        - 'from_username': 付款人姓名
        - 'to_username': 收款人姓名
        - 'amount': 转账金额（保留2位小数）
    """
    # 初始化每个人的余额：正数表示别人欠他，负数表示他欠别人
    balances = {}
    
    # 1. 处理每一笔消费，计算每个人的余额
    for expense in expenses_data:
        payer_id = expense['user_id']
        amount = expense['amount']
        shares = expense.get('shares', [])  # 分摊信息
        
        # 确保支付者在余额字典中
        if payer_id not in balances:
            balances[payer_id] = 0
        
        # 支付者先收回全部金额（因为他垫付了）
        balances[payer_id] += amount
        
        # 每个参与分摊的人都要扣除应分摊的金额
        for share in shares:
            user_id = share['user_id']
            share_amount = share['share_amount']
            
            # 确保分摊者在余额字典中
            if user_id not in balances:
                balances[user_id] = 0
            
            # 扣除应分摊的金额
            balances[user_id] -= share_amount
    
    # 2. 分离债务人和债权人
    debtors = []  # 欠款人：(user_id, 欠款金额)
    creditors = []  # 债权人：(user_id, 应收金额)
    
    for user_id, balance in balances.items():
        if balance < -0.01:  # 避免浮点数误差
            # 欠款人：金额取绝对值（方便计算）
            debtors.append((user_id, abs(balance)))
        elif balance > 0.01:  # 避免浮点数误差
            # 债权人
            creditors.append((user_id, balance))
    
    # 3. 计算最终转账方案 - 使用优化算法减少转账次数
    settlements = []
    
    # 将债权人按应收金额降序排列，优先处理大额债权
    creditors.sort(key=lambda x: x[1], reverse=True)
    # 将债务人按欠款金额降序排列，优先处理大额债务
    debtors.sort(key=lambda x: x[1], reverse=True)
    
    # 转换为可修改的列表
    creditors = list(creditors)
    debtors = list(debtors)
    
    # 贪心算法：每次尽可能匹配最大的债务和债权
    while debtors and creditors:
        # 找到最大的债务人和债权人
        debtor_id, debt_amount = debtors[0]
        creditor_id, credit_amount = creditors[0]
        
        # 如果金额太小，跳过
        if debt_amount <= 0.01 or credit_amount <= 0.01:
            if debt_amount <= 0.01:
                debtors.pop(0)
            if credit_amount <= 0.01:
                creditors.pop(0)
            continue
        
        # 计算转账金额
        transfer = min(debt_amount, credit_amount)
        
        # 记录转账
        if transfer > 0.01:
            settlements.append({
                'from_user_id': debtor_id,
                'to_user_id': creditor_id,
                'from_username': user_map.get(debtor_id, f'用户{debtor_id}'),
                'to_username': user_map.get(creditor_id, f'用户{creditor_id}'),
                'amount': round(transfer, 2)
            })
        
        # 更新余额
        new_debt = debt_amount - transfer
        new_credit = credit_amount - transfer
        
        # 更新或移除已清偿的记录
        if new_debt <= 0.01:
            debtors.pop(0)
        else:
            debtors[0] = (debtor_id, new_debt)
        
        if new_credit <= 0.01:
            creditors.pop(0)
        else:
            creditors[0] = (creditor_id, new_credit)
        
        # 重新排序以保持优先级
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)
    
    return settlements


def main():
    # 示例：4人非均匀分摊场景
    expenses = [
        # A支付400元，A、B、C三人参与分摊
        {
            'payer': 'A',
            'amount': 400,
            'shares': ['A', 'B', 'C']
        },
        # B支付300元，A、B、D三人参与分摊
        {
            'payer': 'B',
            'amount': 300,
            'shares': ['A', 'B', 'D']
        },
        # C支付200元，C、D两人参与分摊
        {
            'payer': 'C',
            'amount': 200,
            'shares': ['C', 'D']
        },
        # D支付100元，四人共同参与分摊
        {
            'payer': 'D',
            'amount': 100,
            'shares': ['A', 'B', 'C', 'D']
        }
    ]
    
    # 计算结算方案
    settlements = calculate_settlements(expenses)
    
    # 输出结果
    print("费用分摊结算方案：")
    for item in settlements:
        print(f"{item['from']} 需向 {item['to']} 支付 {item['amount']} 元")


if __name__ == "__main__":
    main()
