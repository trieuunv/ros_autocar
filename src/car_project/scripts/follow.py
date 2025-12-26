#!/usr/bin/env python3
import rospy
import math
import tf
import numpy as np
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

class StrategicFollower:
    def __init__(self):
        rospy.init_node('follower_node')
        self.pub = rospy.Publisher('/follower/cmd_vel', Twist, queue_size=10)
        
        rospy.Subscriber('/leader/odom', Odometry, self.leader_cb)
        rospy.Subscriber('/follower/odom', Odometry, self.follower_cb)
        rospy.Subscriber('/follower/scan', LaserScan, self.scan_cb)

        self.leader_pose = None
        self.follower_pos = None
        self.f_yaw = 0.0
        self.scan_ranges = []
        
        # THAM SỐ CHIẾN THUẬT
        self.SAFE_FOLLOW = 1.5
        self.MAX_SPEED = 0.7
        self.last_v = 0.0

    def leader_cb(self, msg): self.leader_pose = msg.pose.pose
    def follower_cb(self, msg):
        self.follower_pos = msg.pose.pose.position
        q = msg.pose.pose.orientation
        _, _, self.f_yaw = tf.transformations.euler_from_quaternion([q.x, q.y, q.z, q.w])

    def scan_cb(self, msg):
        self.scan_ranges = np.array(msg.ranges)
        self.scan_ranges = np.where(np.isinf(self.scan_ranges), 10.0, self.scan_ranges)

    def run(self):
        rate = rospy.Rate(20)
        while not rospy.is_shutdown():
            if self.leader_pose and self.follower_pos and len(self.scan_ranges) > 0:
                # 1. TÍNH TOÁN HƯỚNG LEADER
                l_q = self.leader_pose.orientation
                _, _, l_yaw = tf.transformations.euler_from_quaternion([l_q.x, l_q.y, l_q.z, l_q.w])
                tx = self.leader_pose.position.x - 0.4 * math.cos(l_yaw)
                ty = self.leader_pose.position.y - 0.4 * math.sin(l_yaw)
                dist_l = math.sqrt((tx - self.follower_pos.x)**2 + (ty - self.follower_pos.y)**2)
                angle_l = math.atan2(ty - self.follower_pos.y, tx - self.follower_pos.x) - self.f_yaw
                angle_l = math.atan2(math.sin(angle_l), math.cos(angle_l))

                # 2. CHẤM ĐIỂM 9 PHÂN VÙNG (Mỗi vùng 20 độ)
                num_sectors = 9
                sector_size = 180 // num_sectors
                best_score = -999
                best_angle = 0
                best_dist = 0

                for i in range(num_sectors):
                    # Tính toán dải quét cho từng phân vùng
                    start_idx = i * 20
                    end_idx = (i + 1) * 20
                    sector_dist = min(self.scan_ranges[start_idx:end_idx])
                    
                    # Tính góc trung tâm của phân vùng đó (so với xe)
                    # LiDAR quét từ phải (-90) sang trái (+90)
                    sector_angle_rel = math.radians(-90 + (i * 20) + 10)
                    
                    # Lọc Leader: Nếu khoảng cách vùng này giống khoảng cách Leader, coi như rất trống
                    effective_dist = sector_dist
                    if abs(sector_dist - dist_l) < 0.5:
                        effective_dist = 10.0 # Ưu tiên cực cao vì đây là lối đi đến Leader

                    # --- CÔNG THỨC CHẤM ĐIỂM CHIẾN THUẬT ---
                    # Điểm = (Độ trống * Trọng số) + (Độ khớp hướng Leader * Trọng số)
                    # Chúng ta dùng cos để tính độ khớp hướng (càng gần 0 độ lệch, cos càng gần 1)
                    angle_diff = sector_angle_rel - angle_l
                    score = (effective_dist * 1.2) + (math.cos(angle_diff) * 2.5)

                    if score > best_score:
                        best_score = score
                        best_angle = sector_angle_rel
                        best_dist = effective_dist

                # 3. RA QUYẾT ĐỊNH DỰA TRÊN VÙNG TỐT NHẤT
                cmd = Twist()
                
                # PHANH ABS: Nếu vùng tốt nhất vẫn quá sát vật cản thực tế (không phải leader)
                real_min_front = min(self.scan_ranges[70:110])
                if real_min_front < 0.6 and abs(real_min_front - dist_l) > 0.4:
                    cmd.linear.x = -0.4
                    cmd.angular.z = 1.0 if angle_l < 0 else -1.0
                    rospy.logwarn("VAT CAN CHAN DUONG! Dang lui tim loi thoat.")
                
                else:
                    # TIẾN THEO VÙNG CHIẾN THUẬT
                    # Nếu dist_l gần SAFE_FOLLOW thì dừng, nếu xa thì tiến
                    if dist_l > self.SAFE_FOLLOW + 0.1:
                        # Tốc độ phụ thuộc vào độ trống của vùng đã chọn
                        cmd.linear.x = min(self.MAX_SPEED, 0.4 * (dist_l - self.SAFE_FOLLOW))
                        # Nếu đường trước mặt hẹp, tự động giảm tốc
                        if best_dist < 1.5: cmd.linear.x *= 0.5 
                    elif dist_l < self.SAFE_FOLLOW - 0.1:
                        cmd.linear.x = -0.3
                    
                    # Xoay theo góc của phân vùng tốt nhất
                    cmd.angular.z = 3.5 * best_angle

                # 4. LÀM MƯỢT
                self.last_v = 0.4 * cmd.linear.x + 0.6 * self.last_v
                final_cmd = Twist()
                final_cmd.linear.x = self.last_v
                final_cmd.angular.z = cmd.angular.z
                self.pub.publish(final_cmd)

            rate.sleep()

if __name__ == '__main__':
    try:
        StrategicFollower().run()
    except rospy.ROSInterruptException:
        pass
