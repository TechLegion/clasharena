import api from '../api'

export interface TaskStatus {
  task_id: string
  status: 'pending' | 'progress' | 'success' | 'failure'
  result?: any
  error?: string
}

export const taskService = {
  // Get task status
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    const response = await api.get(`/tasks/task/${taskId}`)
    return response.data
  },

  // Poll task until completion
  async pollTask(taskId: string, maxAttempts: number = 30, intervalMs: number = 1000): Promise<any> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await this.getTaskStatus(taskId)
      
      if (status.status === 'success') {
        return status.result
      } else if (status.status === 'failure') {
        throw new Error(status.error || 'Task failed')
      }
      
      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, intervalMs))
    }
    
    throw new Error('Task polling timeout')
  },

  // Cancel a task
  async cancelTask(taskId: string): Promise<void> {
    await api.delete(`/tasks/task/${taskId}`)
  }
}
