<template>
  <div class="users-container">
    <el-card class="filter-container">
      <div class="filter-wrapper">
        <el-input
          v-model="searchQuery"
          placeholder="搜索用户名/邮箱"
          class="search-input"
          clearable
          @clear="handleSearch"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>添加用户
        </el-button>
      </div>
    </el-card>

    <el-card class="table-container">
      <el-table
        v-loading="loading"
        :data="filteredUsers"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" sortable />
        <el-table-column prop="username" label="用户名" sortable />
        <el-table-column prop="email" label="邮箱" sortable />
        <el-table-column prop="role" label="角色" width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'success'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '已激活' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                type="primary"
                :icon="Edit"
                @click="handleEdit(row)"
                v-if="canEdit(row)"
                >编辑</el-button
              >
              <el-button
                type="danger"
                :icon="Delete"
                @click="handleDelete(row)"
                v-if="canDelete(row)"
                >删除</el-button
              >
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 用户表单对话框 -->
    <el-dialog
      :title="dialogType === 'add' ? '添加用户' : '编辑用户'"
      v-model="dialogVisible"
      width="500px"
    >
      <el-form
        ref="userFormRef"
        :model="userForm"
        :rules="userFormRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="dialogType === 'add'">
          <el-input v-model="userForm.password" type="password" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="userForm.role" placeholder="请选择角色">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="is_active">
          <el-switch v-model="userForm.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Edit, Delete } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { getUserList, createUser, updateUser, deleteUser } from '@/api/user'

const userStore = useUserStore()

// 数据
const loading = ref(false)
const users = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const dialogType = ref('add')
const userFormRef = ref(null)

// 表单数据
const userForm = ref({
  username: '',
  email: '',
  password: '',
  role: 'user',
  is_active: true
})

// 表单验证规则
const userFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能小于6位', trigger: 'blur' }
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

// 计算属性：过滤后的用户列表
const filteredUsers = computed(() => {
  if (!searchQuery.value) {
    return users.value
  }
  const query = searchQuery.value.toLowerCase()
  return users.value.filter(
    user =>
      user.username.toLowerCase().includes(query) ||
      user.email.toLowerCase().includes(query)
  )
})

// 权限检查函数
const canEdit = (user) => {
  return userStore.userRole === 'admin' && user.username !== 'admin'
}

const canDelete = (user) => {
  return userStore.userRole === 'admin' && user.username !== 'admin' && user.username !== userStore.username
}

// 方法
const loadUsers = async () => {
  loading.value = true
  try {
    const response = await getUserList()
    console.log('获取用户列表响应:', response)
    
    // 检查响应格式，兼容不同的返回结构
    if (Array.isArray(response)) {
      // 如果直接返回数组
      users.value = response
      total.value = response.length
    } else if (response && response.data && Array.isArray(response.data)) {
      // 如果返回标准格式 {status: 'success', data: [...]}
      users.value = response.data
      total.value = response.data.length
    } else if (response && typeof response === 'object') {
      // 尝试将对象转换为数组
      const userArray = Object.values(response).filter(item => 
        item && typeof item === 'object' && 'username' in item
      )
      if (userArray.length > 0) {
        users.value = userArray
        total.value = userArray.length
      } else {
        console.error('无法解析用户数据:', response)
        ElMessage.error('获取用户列表失败: 无法解析数据')
      }
    } else {
      console.error('无效的用户列表数据:', response)
      ElMessage.error('获取用户列表失败: 无效数据')
    }
  } catch (error) {
    console.error('获取用户列表出错:', error)
    ElMessage.error(`获取用户列表失败: ${error.message || '未知错误'}`)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

const handleAdd = () => {
  dialogType.value = 'add'
  userForm.value = {
    username: '',
    email: '',
    password: '',
    role: 'user',
    is_active: true
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogType.value = 'edit'
  userForm.value = { ...row }
  delete userForm.value.password
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确认删除该用户吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteUser(row.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const submitForm = async () => {
  if (!userFormRef.value) return
  
  try {
    await userFormRef.value.validate()
    
    if (dialogType.value === 'add') {
      await createUser(userForm.value)
      ElMessage.success('添加成功')
    } else {
      const { id } = userForm.value
      await updateUser(id, userForm.value)
      ElMessage.success('更新成功')
    }
    
    dialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error(dialogType.value === 'add' ? '添加失败' : '更新失败')
  }
}

const formatDate = (date) => {
  return new Date(date).toLocaleString()
}

// 生命周期钩子
onMounted(() => {
  loadUsers()
})
</script>

<style lang="scss" scoped>
.users-container {
  padding: 20px;
  
  .filter-container {
    margin-bottom: 20px;
    
    .filter-wrapper {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .search-input {
        width: 300px;
      }
    }
  }
  
  .table-container {
    margin-bottom: 20px;
  }
  
  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 