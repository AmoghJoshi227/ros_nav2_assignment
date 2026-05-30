#!/usr/bin/env python3

import argparse
import math
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose


class NavGoalSender(Node):

    def __init__(self):
        super().__init__('testbed_nav_goal_sender')
        self._action_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose'
        )

    def send_goal(self, x, y, yaw, frame_id='map'):
        self.get_logger().info('Waiting for bt_navigator action server ...')
        self._action_client.wait_for_server()

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = PoseStamped()
        goal_msg.pose.header.frame_id = frame_id
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()

        goal_msg.pose.pose.position.x = x
        goal_msg.pose.pose.position.y = y
        goal_msg.pose.pose.position.z = 0.0

        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(
            f'Sending goal → x={x:.3f}  y={y:.3f}  yaw={math.degrees(yaw):.1f}°'
        )

        send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self._feedback_callback
        )
        rclpy.spin_until_future_complete(self, send_goal_future)

        goal_handle = send_goal_future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected by bt_navigator!')
            return False

        self.get_logger().info('Goal accepted. Navigating ...')

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        status = result_future.result().status
        if status == 4:
            self.get_logger().info('Goal reached successfully!')
            return True
        else:
            self.get_logger().error(f'Navigation failed with status: {status}')
            return False

    def _feedback_callback(self, feedback_msg):
        dist = feedback_msg.feedback.distance_remaining
        self.get_logger().info(
            f'Distance remaining: {dist:.2f} m',
            throttle_duration_sec=2.0
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description='Send a 2D navigation goal to Testbed-T1.0.0.'
    )
    parser.add_argument('x',   type=float, help='Goal X coordinate (m)')
    parser.add_argument('y',   type=float, help='Goal Y coordinate (m)')
    parser.add_argument('yaw', type=float, nargs='?', default=0.0,
                        help='Goal yaw in radians (default 0.0)')
    parser.add_argument('--name', type=str, default='',
                        help='Optional label for this goal')
    parser.add_argument('--frame', type=str, default='map',
                        help='TF frame (default: map)')
    return parser.parse_args()


def main():
    args = parse_args()

    if args.name:
        print(f'\n── Navigating to: {args.name} ──')

    rclpy.init()
    node = NavGoalSender()

    try:
        success = node.send_goal(args.x, args.y, args.yaw, frame_id=args.frame)
    except KeyboardInterrupt:
        node.get_logger().info('Interrupted by user.')
        success = False
    finally:
        node.destroy_node()
        rclpy.shutdown()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
