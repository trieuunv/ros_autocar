import random

# Tên file xuất ra
FILE_NAME = "complex_maze.world"

world_header = """<?xml version="1.0" ?>
<sdf version="1.5">
  <world name="default">
    <include><uri>model://sun</uri></include>
    <include><uri>model://ground_plane</uri></include>
"""

def create_wall(name, x, y, z, roll, pitch, yaw, length, width, height, material="Gazebo/Grey"):
    return f"""
    <model name='{name}'>
      <static>1</static>
      <pose>{x} {y} {z} {roll} {pitch} {yaw}</pose>
      <link name='link'>
        <collision name='collision'>
          <geometry><box><size>{length} {width} {height}</size></box></geometry>
        </collision>
        <visual name='visual'>
          <geometry><box><size>{length} {width} {height}</size></box></geometry>
          <material><script><uri>file://media/materials/scripts/gazebo.material</uri><name>{material}</name></script></material>
        </visual>
      </link>
    </model>"""

content = world_header

# --- 1. XÂY DỰNG ĐƯỜNG LUỒNG (TUNNEL) ---
# Tường thẳng trái & phải (Bắt đầu từ x=-10 đến x=0)
content += create_wall("tunnel_straight_left", -5, 1.5, 0.5, 0, 0, 0, 10, 0.2, 1, "Gazebo/Bricks")
content += create_wall("tunnel_straight_right", -5, -1.5, 0.5, 0, 0, 0, 10, 0.2, 1, "Gazebo/Bricks")

# Khúc cua (Quẹo lên phía trên y > 0)
content += create_wall("tunnel_corner_1", 0.9, 5, 0.5, 0, 0, 1.57, 10, 0.2, 1, "Gazebo/Bricks")
content += create_wall("tunnel_corner_2", -0.9, 6.5, 0.5, 0, 0, 1.57, 7, 0.2, 1, "Gazebo/Bricks")

# --- 2. XÂY DỰNG TƯỜNG BAO QUANH (BOUNDARY) ---
content += create_wall("border_front", 20, 10, 0.5, 0, 0, 1.57, 40, 0.2, 1, "Gazebo/Wood")
content += create_wall("border_back", -10, 10, 0.5, 0, 0, 1.57, 40, 0.2, 1, "Gazebo/Wood")
content += create_wall("border_left", 5, 30, 0.5, 0, 0, 0, 30, 0.2, 1, "Gazebo/Wood")
content += create_wall("border_right", 5, -10, 0.5, 0, 0, 0, 30, 0.2, 1, "Gazebo/Wood")

# --- 3. VẬT CẢN NGẪU NHIÊN TRONG KHU VỰC MỞ (Sau x > 5) ---
for i in range(15):
    x = random.uniform(5, 20)
    y = random.uniform(0, 25)
    yaw = random.uniform(0, 3.14)
    length = random.uniform(1.5, 4.0)
    content += create_wall(f"rand_wall_{i}", x, y, 0.5, 0, 0, yaw, length, 0.2, 1, "Gazebo/RustySteel")

content += "\n  </world>\n</sdf>"

with open(FILE_NAME, "w") as f:
    f.write(content)

print(f"Chúc mừng ông! File {FILE_NAME} đã được tạo tại thư mục dự án.")
