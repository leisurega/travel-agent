#大模型给出的景点顺序并不是严格按地理位置就近排序的，需要根据腾讯地图API计算路径，并根据路径长度进行排序
import json
import requests
import time
import os
from typing import List, Dict, Optional, Literal

# 配置信息（改用腾讯地图API）
QIANWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "your_dashscope_api_key")  # 千问API密钥（阿里云达摩院）
TENCENT_API_KEY = os.getenv("TENCENT_MAP_API_KEY", "your_tencent_map_api_key")     # 腾讯地图API密钥
# 腾讯地图路径规划API（参考腾讯位置服务文档）
TENCENT_ROUTE_URL = {
    "driving": "https://apis.map.qq.com/ws/direction/v1/driving",  # 驾车路径
    "walking": "https://apis.map.qq.com/ws/direction/v1/walking",  # 步行路径
    "bicycling": "https://apis.map.qq.com/ws/direction/v1/bicycling"  # 骑行路径
}

# 坐标格式说明：统一使用纬度在前格式 [lat, lng]
# 与腾讯地图API格式一致，减少转换

# 腾讯地图POI分类映射（根据大模型返回的type映射到腾讯地图category）
TENCENT_CATEGORY_MAP = {
    "美食": "100000", 
    "购物": "130000", 
    "旅游景点": "220000", 
    "娱乐休闲": "160000",
    "运动健身": "180000",
    "文化场馆": "230000"
    }


class TravelPlanner:
    def __init__(self):
        self.itinerary = {
            "overview": {},
            "days": [],
            "mapSettings": {"recommendedPlaces": True},
            "city": ""  # 新增：存储大模型返回的城市信息
        }

    def generate_itinerary(
        self,
        destination: str,
        days: int,
        interests: List[str],
        start_day: str = "09:00",
        avoid: List[str] = None,
        default_route_mode: Literal["driving", "walking"] = "walking"
    ) -> Dict:
        """生成完整旅行计划（大模型直接返回City，修正MCP API）"""
        # 1. 调用千问：强制返回city字段
        raw_plan = self._call_qianwen_model(destination, days, interests, start_day, avoid)
        # 2. 解析：直接提取大模型返回的city
        parsed_data = self._parse_model_output(raw_plan)
        parsed_days = parsed_data["days"]
        self.itinerary["city"] = parsed_data["city"]  # 无需额外解析，直接赋值
        
        # 3. 补全坐标（用大模型返回的city精准匹配）
        self._complete_coordinates(parsed_days, self.itinerary["city"])
        # 4. 腾讯地图API计算路径
        self._calculate_routes_with_tencent(parsed_days, default_route_mode)
        # 5. 更新overview
        self._update_overview(parsed_days)
        return self.itinerary

    def _call_qianwen_model(self, destination: str, days: int, interests: List[str],
                           start_day: str, avoid: Optional[List[str]]) -> str:
        """Prompt 核心优化：强制大模型返回 city 字段"""
        avoid_str = ", ".join(avoid) if avoid else "无特殊规避项"
        prompt = f"""请生成{destination}{days}天旅行计划，严格按以下JSON格式返回（无任何多余文字）：
{{
  "city": "行程对应的标准城市名（如：杭州市、北京市，必须包含“市”字，直辖市除外）",
  "days": [
    {{
      "day": "DAY N",  // N为1,2,...（按天数递增）
      "theme": "当日主题（如：西湖风光+南宋文化）",
      "attractions": [
        {{
          "id": 1,  // 每天景点ID从1开始重新编号
          "name": "景点名称（如：西湖"）,
          "type": "景点类型（如：旅游景点）",
          "description": "100字内推荐理由+游玩建议（如：清晨人少，适合拍湖景）",
          "image": "null"  // 无图片时固定为null，不填其他内容
        }}
      ]
    }}
  ]
}}
强制要求：
1. 必须包含 "city" 字段，值为标准城市名（如"苏州市""上海市"，不可简写为"苏州""上海"）；
2. 每天3-5个景点，严格按照"地理位置就近"原则排序，相邻景点距离应控制在5公里以内，避免跨区往返；
3. 地点类型需从 [美食，购物，旅游景点，运动健身，文化场馆] 这些类别中选取。优先选择"旅游景点"类型，特别是对于知名景点（如雷峰塔、西湖、断桥等）。首先，要覆盖用户选择的 {','.join (interests)} 兴趣类别；同时，需规避 {avoid_str} 相关内容。若用户选择的兴趣类别数量较少，还需补充选取地点选项中其他类别的地点，以丰富选择。
4. 地点类型如果有歧义，请根据地点名称和地点描述进行判断，如果无法判断，请返回"旅游景点"。对于知名景点，必须使用"旅游景点"类型。
5. 重要：景点排序必须考虑实际地理位置，相近的景点应安排在一起，避免出现距离很近的景点被安排在行程首尾的情况。"""

        # 千问API调用（符合阿里云达摩院官方规范）
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {QIANWEN_API_KEY}"
        }
        payload = {
            "model": "qwen-plus",  # 可选qwen-max（精度更高）/qwen-turbo（速度更快）
            "input": {"prompt": prompt},
            "parameters": {
                "temperature": 0.5,  # 降低随机性，确保格式正确
                "max_tokens": 2048,  # 足够生成3-5天行程
                "response_format": {"type": "json_object"}  # 强制JSON输出
            }
        }
        response = requests.post(
            url="https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=payload
        )
        response_data = response.json()
        # 错误处理：确保模型返回有效结果
        if "output" in response_data and "text" in response_data["output"]:
            return response_data["output"]["text"]
        raise Exception(f"千问调用失败：{json.dumps(response_data, ensure_ascii=False)}")

    def _parse_model_output(self, raw_output: str) -> Dict:
        """解析大模型输出（直接获取city和days）"""
        try:
            # 提取纯JSON片段（避免大模型多输出说明文字）
            json_start = raw_output.find("{")
            json_end = raw_output.rfind("}") + 1
            parsed = json.loads(raw_output[json_start:json_end])
            # 校验关键字段
            if "city" not in parsed or "days" not in parsed:
                raise KeyError("模型输出缺少 'city' 或 'days' 字段")
            return parsed
        except json.JSONDecodeError as e:
            raise Exception(f"JSON解析失败：{str(e)}，原始输出：{raw_output[:500]}")
        except KeyError as e:
            raise Exception(f"字段缺失：{str(e)}，原始输出：{raw_output[:500]}")

    def _complete_coordinates(self, days: List[Dict], city: str) -> None:
        """根据name、city、type获取坐标"""
        for day in days:
            for attr in day["attractions"]:
                # 打印每个地点的type信息
                print(f"[地点信息] {attr['name']} - type: {attr.get('type', '未指定')}")
                
                # 使用新的方法：根据name、city、type获取坐标
                lng_lat = self._get_coordinate_by_place_info(attr["name"], city, attr.get("type", ""))
                if lng_lat is not None:
                    attr["coordinate"] = [lng_lat[1], lng_lat[0]]  # 转换为 [lat, lng] 格式
                else:
                    attr["coordinate"] = [0.0, 0.0]
                    print(f"警告：{attr['name']}（{city}）未找到坐标，原因：腾讯地图地点搜索失败")

    def _get_coordinate_by_place_info(self, name: str, city: str, type_str: str) -> Optional[List[float]]:
        """根据name、city、type获取坐标，使用腾讯地图地点搜索API"""
        # 获取对应的category
        category = TENCENT_CATEGORY_MAP.get(type_str, "")
        
        params = {
            "key": TENCENT_API_KEY,
            "keyword": name,
            "region": city,
            "region_fix": 1,  # 严格限制在指定城市内
            "page_index": 1,  # 页码，从1开始
            "page_size": 1,   # 每页条数，只取第一条结果
            "output": "json"
        }
        
        # 如果有对应的category，添加filter参数
        if category:
            params["filter"] = f"category={category}"
        
        try:
            print(f"[Tencent Place Search] 搜索: {name} in {city}, type={type_str}, category={category}")
            response = requests.get("https://apis.map.qq.com/ws/place/v1/suggestion", params=params, timeout=8)
            data = response.json()
            
            print(f"[Tencent Place Search] 响应: {json.dumps(data, ensure_ascii=False)[:500]}")
            
            if data.get("status") == 0:
                data_list = data.get("data", [])
                if data_list:
                    first_poi = data_list[0]
                    location = first_poi.get("location", {})
                    if location:
                        lng = location.get("lng")
                        lat = location.get("lat")
                        if lng is not None and lat is not None:
                            print(f"[Tencent Place Search] 成功: {name} -> [{lng}, {lat}]")
                            return [lng, lat]  # 统一返回经度在前格式 [lng, lat]
                else:
                    print(f"[Tencent Place Search] 无结果: {name} in {city}")
            else:
                print(f"[Tencent Place Search] 失败: {name}, status={data.get('status')}, message={data.get('message')}")
        except Exception as e:
            print(f"[Tencent Place Search] 异常: {name}, {str(e)}")
        
        return None

    def _tencent_geocode(self, address: str, city: str) -> Optional[List[float]]:
        """调用腾讯地图地理编码API，返回 [lng, lat] 或 None"""
        params = {
            "key": TENCENT_API_KEY,
            "address": f"{city}{address}",
            "output": "json"
        }
        try:
            response = requests.get("https://apis.map.qq.com/ws/geocoder/v1/", params=params, timeout=8)
            data = response.json()
            if data.get("status") == 0:  # 腾讯地图成功状态码为0
                result = data.get("result", {})
                location = result.get("location", {})
                if location:
                    lng = location.get("lng")
                    lat = location.get("lat")
                    if lng is not None and lat is not None:
                        return [lng, lat]
        except Exception as e:
            print(f"腾讯地图地理编码异常：{str(e)}")
        return None

    def _calculate_routes_with_tencent(self, days: List[Dict], default_mode: str) -> None:
        """调用腾讯地图API计算路径"""
        for day in days:
            attractions = day["attractions"]
            for i in range(len(attractions)):
                # 最后一个景点无下一站
                if i >= len(attractions) - 1:
                    attractions[i]["distanceToNext"] = None
                    attractions[i]["durationToNext"] = None
                    attractions[i]["transportationToNext"] = None
                    continue

                curr_coord = attractions[i]["coordinate"]
                next_coord = attractions[i+1]["coordinate"]
                # 跳过坐标异常的景点
                if curr_coord == [0.0, 0.0] or next_coord == [0.0, 0.0]:
                    attractions[i]["distanceToNext"] = "坐标异常"
                    attractions[i]["durationToNext"] = None
                    attractions[i]["transportationToNext"] = None
                    print(f"[Route] 跳过：坐标异常 {curr_coord} -> {next_coord}")
                    continue

                # 1. 先调用步行API判断距离（短途优先步行）
                walking_route = self._call_tencent_route_api("walking", curr_coord, next_coord)
                if walking_route and float(walking_route["distance"]) <= 2000:  # 2公里内步行
                    route_data = walking_route
                    transport_mode = "步行"
                # 2. 长途用默认模式（驾车/公交）
                else:
                    route_data = self._call_tencent_route_api(default_mode, curr_coord, next_coord)
                    transport_mode = "驾车" if default_mode == "driving" else "公交"

                # 解析路径数据（统一格式）
                if route_data:
                    # 距离：米 → 公里（保留1位小数）
                    distance_km = round(float(route_data["distance"]) / 1000, 1)
                    attractions[i]["distanceToNext"] = f"{distance_km}公里"
                    
                    # 时间：腾讯地图API返回的duration单位是分钟，直接使用
                    duration_min = int(float(route_data["duration"]))
                    attractions[i]["durationToNext"] = f"{duration_min}分钟"
                    attractions[i]["transportationToNext"] = transport_mode
                    
                    print(f"[Route] {transport_mode} OK {curr_coord}->{next_coord} distance={attractions[i]['distanceToNext']} duration={attractions[i]['durationToNext']}")
                else:
                    attractions[i]["distanceToNext"] = "路径计算失败"
                    attractions[i]["durationToNext"] = None
                    attractions[i]["transportationToNext"] = None
                    print(f"[Route] 失败 {curr_coord}->{next_coord}")

    def _call_tencent_route_api(self, mode: Literal["driving", "walking"],
                               curr_coord: List[float], next_coord: List[float]) -> Optional[Dict]:
        """调用腾讯地图路径规划API，返回 {distance, duration}。"""
        # 统一使用纬度在前格式 [lat, lng]，直接使用无需转换
        origin = f"{curr_coord[0]},{curr_coord[1]}"  # [lat, lng] -> "lat,lng"
        destination = f"{next_coord[0]},{next_coord[1]}"

        params = {
            "key": TENCENT_API_KEY,
            "from": origin,
            "to": destination,
            "output": "json"
        }
        try:
            print(f"[Tencent][{mode}] 调用 {origin}->{destination}")
            resp = requests.get(TENCENT_ROUTE_URL[mode], params=params, timeout=10)
            data = resp.json()
            try:
                raw = json.dumps(data, ensure_ascii=False)
                print(f"[Tencent][{mode}] 响应JSON {origin}->{destination}: {raw[:2000]}")
            except Exception:
                pass
        except Exception as e:
            print(f"[Tencent][{mode}] 调用异常：{str(e)} {origin}->{destination}")
            return None

        if data.get("status") == 0:  # 腾讯地图成功状态码为0
            result = data.get("result", {})
            routes = result.get("routes", [])
            if routes:
                first = routes[0]
                distance = first.get("distance")
                duration = first.get("duration")
                # 腾讯地图duration单位：驾车为秒，步行为分钟
                if distance is not None and duration is not None:
                    print(f"[Tencent][{mode}] 成功 distance={distance} duration={duration} {origin}->{destination}")
                    return {"distance": str(distance), "duration": str(duration)}
                print(f"[Tencent][{mode}] 有routes但缺字段 keys={list(first.keys())} {origin}->{destination}")
                return None
        print(f"[Tencent][{mode}] 失败 status={data.get('status')} message={data.get('message')} {origin}->{destination}")
        return None

    def _update_overview(self, parsed_days: List[Dict]) -> None:
        """同步更新overview（按days顺序）"""
        self.itinerary["days"] = parsed_days
        # 生成每日景点概览
        for day in parsed_days:
            day_key = day["day"]
            self.itinerary["overview"][day_key] = [attr["name"] for attr in day["attractions"]]
        # 添加待规划字段
        self.itinerary["overview"]["待规划"] = []


# 使用示例
if __name__ == "__main__":
    planner = TravelPlanner()
    try:
        # 测试：输入模糊目的地（大模型会自动返回正确city）
        itinerary = planner.generate_itinerary(
            destination="西湖",  # 无需输入“杭州市”，大模型会返回“杭州市”
            days=1,
            interests=["自然景观", "本地美食"],
            start_day="2025-09-12",
            avoid=["高强度运动", "夜间偏僻景点"],
            default_route_mode="driving"
        )
        # 保存结果
        with open("hangzhou_travel.json", "w", encoding="utf-8") as f:
            json.dump(itinerary, f, ensure_ascii=False, indent=2)
        print("✅ 行程生成成功！")
        print(f"📌 行程城市：{itinerary['city']}")
        print("\n📅 行程概览：")
        for day, spots in itinerary["overview"].items():
            if spots:
                print(f"{day}：{', '.join(spots)}")
    except Exception as e:
        print(f"❌ 执行失败：{str(e)}")