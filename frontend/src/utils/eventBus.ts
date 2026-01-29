/**
 * 事件总线
 * 用于组件/Store 之间的解耦通信
 */

/**
 * 应用事件类型定义
 */
export type AppEvents = {
  // 用户相关事件
  'user:logout': void
  'user:login': { userId: number }

  // 项目相关事件
  'project:change': { projectId: number }
  'project:sync': { projectId: number }
}

/**
 * 事件处理函数类型
 */
type EventHandler<T = unknown> = (data: T) => void

/**
 * 简单的事件总线实现
 */
class EventBus {
  private events: Map<string, EventHandler[]> = new Map()

  /**
   * 订阅事件
   */
  on<K extends keyof AppEvents>(event: K, handler: EventHandler<AppEvents[K]>): void {
    if (!this.events.has(event)) {
      this.events.set(event, [])
    }
    this.events.get(event)!.push(handler as EventHandler)
  }

  /**
   * 取消订阅事件
   */
  off<K extends keyof AppEvents>(event: K, handler: EventHandler<AppEvents[K]>): void {
    const handlers = this.events.get(event)
    if (handlers) {
      const index = handlers.indexOf(handler as EventHandler)
      if (index > -1) {
        handlers.splice(index, 1)
      }
    }
  }

  /**
   * 触发事件
   */
  emit<K extends keyof AppEvents>(event: K, data: AppEvents[K]): void
  emit<K extends keyof AppEvents>(event: K, ...args: AppEvents[K] extends void ? [] : [AppEvents[K]]): void {
    const handlers = this.events.get(event)
    if (handlers) {
      const data = args[0]
      handlers.forEach((handler) => handler(data))
    }
  }

  /**
   * 清除所有事件监听器
   */
  clear(): void {
    this.events.clear()
  }
}

/**
 * 事件总线实例
 */
export const eventBus = new EventBus()
