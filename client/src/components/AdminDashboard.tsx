import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

interface User {
  user_id: string;
  name: string;
  risk_score: number;
  status?: string;
  account_age_days?: number;
  typology?: string;
  is_suspicious?: number;
  balance?: number;
  created_at?: string;
  transaction_count?: number;
  monthly_spending?: number;
  total_transactions?: number;
}

interface Transaction {
  transaction_id: string;
  source_user_id: string;
  target_user_id: string;
  amount: number;
  status: string;
  timestamp: string;
  ai_risk_score?: number;
  is_suspicious?: number;
}

interface FraudResult {
  user_id: string;
  risk_probability: number;
  risk_level: string;
  primary_flag?: string;
  contributing_factors: Array<{
    factor_type: string;
    description: string;
    severity: string;
  }>;
}

interface AuditLog {
  log_type: string;
  description: string;
  details?: {
    path?: string[];
    transactions?: Array<{ amount: number; timestamp: string }>;
    ai_risk_score?: number;
  };
  timestamp: string;
}

type ViewMode = 'transactions' | 'risk-alerts' | 'users';

export default function AdminDashboard() {
  const [viewMode, setViewMode] = useState<ViewMode>('transactions');
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [flaggedUsers, setFlaggedUsers] = useState<User[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [fraudResult, setFraudResult] = useState<FraudResult | null>(null);
  const [showAuditModal, setShowAuditModal] = useState(false);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [amountFilter, setAmountFilter] = useState<string>('all');
  const [dateFilter, setDateFilter] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 20;

  useEffect(() => {
    loadTransactions();
    loadFlaggedUsers();
    loadUsers();
  }, []);

  const loadTransactions = async () => {
    try {
      const response = await axios.get(`${API_BASE}/transactions`);
      setTransactions(Array.isArray(response.data) ? response.data : []);
    } catch (error) {
      console.error('Error loading transactions:', error);
    }
  };

  const loadFlaggedUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/users`, {
        params: { risk_filter: 'suspicious', limit: 100 }
      });
      const usersData = Array.isArray(response.data) ? response.data : response.data.users || [];
      setFlaggedUsers(usersData.filter((u: User) => u.is_suspicious === 1 || u.risk_score > 0.7));
    } catch (error) {
      console.error('Error loading flagged users:', error);
    }
  };

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/users`, {
        params: { limit: 100, offset: currentPage * pageSize, search: searchTerm || undefined }
      });
      setUsers(Array.isArray(response.data) ? response.data : response.data.users || []);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const analyzeUser = async (user: User) => {
    setSelectedUser(user);
    try {
      // Load full user data with transaction count
      const userResponse = await axios.get(`${API_BASE}/users/${user.user_id}`);
      setSelectedUser(userResponse.data);
      
      // Load fraud analysis
      const response = await axios.get(`${API_BASE}/detect-fraud/${user.user_id}`);
      setFraudResult(response.data);
      await loadAuditLogs(user.user_id);
    } catch (error: any) {
      console.error('Error analyzing user:', error);
      if (error.response?.status === 404) {
        alert(`User ${user.user_id} not found in database.`);
        setSelectedUser(null);
        setFraudResult(null);
      }
    }
  };

  const handleApprove = async (userId: string) => {
    try {
      // Approve appeal and unfreeze user
      await axios.post(`${API_BASE}/admin/approve-appeal/${userId}`);
      await loadFlaggedUsers();
      await loadUsers();
      setSelectedUser(null);
      setFraudResult(null);
      alert('Appeal approved. User account unfrozen.');
    } catch (error) {
      console.error('Error approving:', error);
    }
  };

  const loadAuditLogs = async (userId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/audit-logs/${userId}`);
      setAuditLogs(response.data);
    } catch (error) {
      console.error('Error loading audit logs:', error);
      setAuditLogs([]);
    }
  };

  const handleRejectAppeal = async (userId: string) => {
    if (!confirm('Are you sure you want to reject this appeal? The user will remain frozen permanently.')) {
      return;
    }
    try {
      await axios.post(`${API_BASE}/admin/reject-appeal/${userId}`);
      await loadFlaggedUsers();
      setSelectedUser(null);
      setFraudResult(null);
      alert('Appeal rejected. User remains frozen.');
    } catch (error) {
      console.error('Error rejecting appeal:', error);
    }
  };

  const handleFreeze = async (userId: string) => {
    try {
      await axios.post(`${API_BASE}/admin/freeze-user/${userId}`);
      await loadFlaggedUsers();
      await loadUsers();
      if (selectedUser?.user_id === userId) {
        const updated = await axios.get(`${API_BASE}/users/${userId}`);
        setSelectedUser(updated.data);
      }
      alert('Account frozen successfully.');
    } catch (error) {
      console.error('Error freezing:', error);
    }
  };

  const handleBlock = async (userId: string) => {
    try {
      await axios.post(`${API_BASE}/admin/block-user/${userId}`);
      await loadFlaggedUsers();
      setSelectedUser(null);
      setFraudResult(null);
      alert('Account permanently blocked.');
    } catch (error) {
      console.error('Error blocking:', error);
    }
  };

  const getRiskColor = (score: number): string => {
    if (score >= 0.7) return 'text-red-400';
    if (score >= 0.4) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'FLAGGED': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500';
      case 'BLOCKED': return 'bg-red-500/20 text-red-400 border-red-500';
      case 'APPROVED': return 'bg-green-500/20 text-green-400 border-green-500';
      default: return 'bg-slate-500/20 text-slate-400 border-slate-500';
    }
  };

  const filteredTransactions = transactions.filter(tx => {
    if (statusFilter !== 'all' && tx.status !== statusFilter) return false;
    if (amountFilter === 'high' && tx.amount < 10000) return false;
    if (amountFilter === 'medium' && (tx.amount < 1000 || tx.amount >= 10000)) return false;
    if (amountFilter === 'low' && tx.amount >= 1000) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">Analyst Command Center</h1>
            <p className="text-slate-400 text-sm">Money Laundering Detection System</p>
          </div>
          <button
            onClick={() => {
              localStorage.removeItem('token');
              localStorage.removeItem('user');
              window.location.href = '/login';
            }}
            className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-sm font-medium"
          >
            Logout
          </button>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar Navigation */}
        <aside className="w-64 bg-slate-800 border-r border-slate-700 p-4">
          <nav className="space-y-2">
            <button
              onClick={() => setViewMode('transactions')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                viewMode === 'transactions' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700'
              }`}
            >
              Transaction Monitor
            </button>
            <button
              onClick={() => setViewMode('risk-alerts')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                viewMode === 'risk-alerts' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700'
              }`}
            >
              Risk Alerts ({flaggedUsers.length})
            </button>
            <button
              onClick={() => setViewMode('users')}
              className={`w-full text-left px-4 py-2 rounded-lg transition-colors ${
                viewMode === 'users' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-700'
              }`}
            >
              User Management
            </button>
          </nav>

          {/* User List (Fixed Height, Scrollable) */}
          {viewMode === 'users' && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-400 mb-2">Users</h3>
              <input
                type="text"
                placeholder="Search users..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(0);
                }}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm mb-3"
              />
              <div className="h-96 overflow-y-auto space-y-2">
                {users.map(user => (
                  <div
                    key={user.user_id}
                    onClick={() => analyzeUser(user)}
                    className={`p-2 rounded cursor-pointer transition-colors ${
                      selectedUser?.user_id === user.user_id
                        ? 'bg-blue-600/20 border border-blue-500'
                        : 'bg-slate-900 hover:bg-slate-700 border border-slate-700'
                    }`}
                  >
                    <div className="text-xs font-semibold">{user.user_id}</div>
                    <div className="text-xs text-slate-400 truncate">{user.name}</div>
                    <div className={`text-xs font-semibold ${getRiskColor(user.risk_score)}`}>
                      {(user.risk_score * 100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          {/* Transaction Monitor */}
          {viewMode === 'transactions' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Transaction Monitor</h2>
              
              {/* Filters */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                >
                  <option value="all">All Status</option>
                  <option value="PENDING">Pending</option>
                  <option value="APPROVED">Approved</option>
                  <option value="FLAGGED">Flagged</option>
                  <option value="BLOCKED">Blocked</option>
                </select>
                
                <select
                  value={amountFilter}
                  onChange={(e) => setAmountFilter(e.target.value)}
                  className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                >
                  <option value="all">All Amounts</option>
                  <option value="high">High ($10k+)</option>
                  <option value="medium">Medium ($1k-$10k)</option>
                  <option value="low">Low (&lt;$1k)</option>
                </select>
                
                <input
                  type="date"
                  className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                />
                
                <input
                  type="text"
                  placeholder="Search transactions..."
                  className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                />
              </div>

              {/* Transactions Table - Fixed Height with Scroll */}
              <div className="bg-slate-800 rounded-lg border border-slate-700 overflow-hidden">
                <div className="h-[500px] overflow-y-auto">
                  <table className="w-full">
                    <thead className="bg-slate-900 sticky top-0 z-10">
                      <tr>
                        <th className="px-4 py-3 text-left text-sm font-semibold bg-slate-900">Transaction ID</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold bg-slate-900">From</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold bg-slate-900">To</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold bg-slate-900">Amount</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold bg-slate-900">Status</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold bg-slate-900">AI Risk</th>
                        <th className="px-4 py-3 text-left text-sm font-semibold bg-slate-900">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredTransactions.map(tx => (
                        <tr key={tx.transaction_id} className="border-t border-slate-700 hover:bg-slate-700/50">
                          <td className="px-4 py-3 text-sm font-mono">{tx.transaction_id}</td>
                          <td className="px-4 py-3 text-sm">{tx.source_user_id}</td>
                          <td className="px-4 py-3 text-sm">{tx.target_user_id}</td>
                          <td className="px-4 py-3 text-sm font-semibold">${tx.amount.toLocaleString()}</td>
                          <td className="px-4 py-3">
                            <span className={`px-2 py-1 rounded text-xs border ${getStatusColor(tx.status)}`}>
                              {tx.status}
                            </span>
                          </td>
                          <td className={`px-4 py-3 text-sm font-semibold ${getRiskColor(tx.ai_risk_score || 0)}`}>
                            {((tx.ai_risk_score || 0) * 100).toFixed(0)}%
                          </td>
                          <td className="px-4 py-3 text-sm text-slate-400">
                            {new Date(tx.timestamp).toLocaleDateString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Risk Alerts Stats */}
          {viewMode === 'risk-alerts' && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
                <div className="text-sm text-slate-400 mb-1">Flagged Users</div>
                <div className="text-2xl font-bold text-yellow-400">{flaggedUsers.length}</div>
              </div>
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
                <div className="text-sm text-slate-400 mb-1">Frozen Accounts</div>
                <div className="text-2xl font-bold text-red-400">
                  {flaggedUsers.filter(u => u.status === 'FROZEN').length}
                </div>
              </div>
              <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
                <div className="text-sm text-slate-400 mb-1">Avg Risk Score</div>
                <div className="text-2xl font-bold text-orange-400">
                  {flaggedUsers.length > 0 
                    ? ((flaggedUsers.reduce((sum, u) => sum + u.risk_score, 0) / flaggedUsers.length) * 100).toFixed(0)
                    : 0}%
                </div>
              </div>
            </div>
          )}

          {/* Risk Alerts */}
          {viewMode === 'risk-alerts' && (
            <div>
              <h2 className="text-xl font-semibold mb-4">Risk Alerts - Flagged Users</h2>
              
              {/* Fixed Height Scrollable Container */}
              <div className="h-[500px] overflow-y-auto">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {flaggedUsers.map(user => (
                    <div
                      key={user.user_id}
                      className="bg-slate-800 rounded-lg border border-slate-700 p-6 cursor-pointer hover:border-blue-500 transition-colors"
                      onClick={() => analyzeUser(user)}
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <div className="text-lg font-semibold">{user.name}</div>
                          <div className="text-sm text-slate-400 font-mono">{user.user_id}</div>
                        </div>
                        <div className={`text-2xl font-bold ${getRiskColor(user.risk_score)}`}>
                          {(user.risk_score * 100).toFixed(0)}%
                        </div>
                      </div>
                      
                      {user.typology && (
                        <div className="mb-2">
                          <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">
                            {user.typology}
                          </span>
                        </div>
                      )}
                      
                      <div className="text-sm text-slate-400">
                        Status: <span className="text-white">{user.status || 'ACTIVE'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* User Account Details */}
          {selectedUser && (
            <div className="mt-6 bg-slate-800 rounded-lg border border-slate-700 p-6">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-2xl font-bold mb-2">{selectedUser.name}</h3>
                  <div className="text-sm text-slate-400 font-mono">{selectedUser.user_id}</div>
                </div>
                <div className="flex gap-3">
                  {selectedUser.status === 'FROZEN' ? (
                    <button
                      onClick={() => handleApprove(selectedUser.user_id)}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium"
                    >
                      Unfreeze Account
                    </button>
                  ) : (
                    <button
                      onClick={() => handleFreeze(selectedUser.user_id)}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium"
                    >
                      Freeze Account
                    </button>
                  )}
                </div>
              </div>

              {/* Account Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                  <div className="text-xs text-slate-400 mb-1">Risk Score</div>
                  <div className={`text-2xl font-bold ${getRiskColor(selectedUser.risk_score)}`}>
                    {(selectedUser.risk_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                  <div className="text-xs text-slate-400 mb-1">Account Status</div>
                  <div className={`text-lg font-semibold ${
                    selectedUser.status === 'FROZEN' ? 'text-red-400' : 
                    selectedUser.status === 'BLOCKED' ? 'text-red-600' : 'text-green-400'
                  }`}>
                    {selectedUser.status || 'ACTIVE'}
                  </div>
                </div>
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                  <div className="text-xs text-slate-400 mb-1">Account Age</div>
                  <div className="text-lg font-semibold text-white">
                    {selectedUser.account_age_days || 0} days
                  </div>
                  {selectedUser.created_at && (
                    <div className="text-xs text-slate-500 mt-1">
                      Created: {new Date(selectedUser.created_at).toLocaleDateString()}
                    </div>
                  )}
                </div>
                <div className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                  <div className="text-xs text-slate-400 mb-1">Transactions</div>
                  <div className="text-lg font-semibold text-white">
                    {selectedUser.transaction_count || 0}
                  </div>
                </div>
              </div>

              {/* Risk Score Visual Graph */}
              <div className="mb-6">
                <div className="text-sm font-semibold text-slate-300 mb-2">Risk Score Visualization</div>
                <div className="h-8 bg-slate-900 rounded-full overflow-hidden border border-slate-700">
                  <div
                    className="h-full transition-all duration-500"
                    style={{
                      width: `${(selectedUser.risk_score * 100)}%`,
                      backgroundColor: selectedUser.risk_score >= 0.7 ? '#ef4444' :
                                     selectedUser.risk_score >= 0.4 ? '#f59e0b' : '#22c55e'
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-400 mt-1">
                  <span>Low (0%)</span>
                  <span>Medium (50%)</span>
                  <span>High (100%)</span>
                </div>
              </div>

              {/* Transaction Volume Graph */}
              {(selectedUser.transaction_count || 0) > 0 && (
                <div className="mb-6">
                  <div className="text-sm font-semibold text-slate-300 mb-2">Transaction Activity (Last 7 Days)</div>
                  <div className="h-32 bg-slate-900 rounded-lg p-4 border border-slate-700 flex items-end justify-between gap-2">
                    {Array.from({ length: 7 }).map((_, i) => {
                      // Mock data - in real app, would fetch actual daily transaction counts
                      const txCount = selectedUser.transaction_count || 0;
                      const dayTransactions = Math.floor(txCount / 7) + Math.floor(Math.random() * 3);
                      const maxHeight = Math.max(txCount, 10);
                      const height = Math.min((dayTransactions / maxHeight) * 100, 100);
                      return (
                        <div key={i} className="flex-1 flex flex-col items-center">
                          <div
                            className="w-full bg-blue-500 rounded-t transition-all min-h-[4px]"
                            style={{ height: `${Math.max(height, 4)}%` }}
                            title={`${dayTransactions} transactions`}
                          />
                          <div className="text-xs text-slate-400 mt-1">D{i+1}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* AI Decision Support */}
          {selectedUser && fraudResult && (
            <div className="mt-6 bg-slate-800 rounded-lg border border-slate-700 p-6">
              <h3 className="text-lg font-semibold mb-4">AI Decision Support</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                <div>
                  <div className="text-sm text-slate-400 mb-1">AI Risk Score</div>
                  <div className={`text-4xl font-bold ${getRiskColor(fraudResult.risk_probability)}`}>
                    {(fraudResult.risk_probability * 100).toFixed(0)}%
                  </div>
                  <div className="text-sm text-slate-400 mt-1">{fraudResult.risk_level.toUpperCase()} RISK</div>
                </div>
                
                <div>
                  <div className="text-sm text-slate-400 mb-1">Typology Detected</div>
                  <div className="text-xl font-semibold text-red-400">
                    {fraudResult.primary_flag || 'None'}
                  </div>
                </div>
              </div>

              {fraudResult.contributing_factors && fraudResult.contributing_factors.length > 0 && (
                <div className="mb-6">
                  <div className="text-sm font-semibold text-slate-300 mb-2">Contributing Factors</div>
                  <div className="space-y-2">
                    {fraudResult.contributing_factors.map((factor, i) => (
                      <div
                        key={i}
                        className="p-3 bg-slate-900 rounded-lg border-l-4"
                        style={{
                          borderColor:
                            factor.severity === 'critical' ? '#ef4444' :
                            factor.severity === 'high' ? '#f59e0b' :
                            factor.severity === 'medium' ? '#eab308' : '#22c55e'
                        }}
                      >
                        <div className="text-xs font-semibold text-slate-400 uppercase mb-1">
                          {factor.factor_type}
                        </div>
                        <div className="text-sm text-white">{factor.description}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Show pending appeal if user is frozen */}
              {selectedUser.status === 'FROZEN' && (
                <div className="mb-6 p-4 bg-yellow-500/20 border border-yellow-500 rounded-lg">
                  <div className="text-sm font-semibold text-yellow-400 mb-2">Pending Appeal</div>
                  <div className="text-sm text-slate-300">
                    This user has submitted an appeal. Review the audit logs and make a decision.
                  </div>
                </div>
              )}

              <div className="flex gap-3 mb-4">
                <button
                  onClick={() => setShowAuditModal(true)}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium"
                >
                  View Audit Logs
                </button>
              </div>

              <div className="flex gap-3 flex-wrap">
                <button
                  onClick={() => setShowAuditModal(true)}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium"
                >
                  View Audit Logs
                </button>
                {selectedUser.status === 'FROZEN' && (
                  <>
                    <button
                      onClick={() => handleApprove(selectedUser.user_id)}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium"
                    >
                      Approve Appeal / Unfreeze
                    </button>
                    <button
                      onClick={() => handleRejectAppeal(selectedUser.user_id)}
                      className="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg font-medium"
                    >
                      Reject Appeal
                    </button>
                  </>
                )}
                {selectedUser.status !== 'FROZEN' && selectedUser.status !== 'BLOCKED' && (
                  <button
                    onClick={() => handleFreeze(selectedUser.user_id)}
                    className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg font-medium"
                  >
                    Freeze Account
                  </button>
                )}
                <button
                  onClick={() => handleBlock(selectedUser.user_id)}
                  className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg font-medium"
                >
                  Permanent Block
                </button>
              </div>
            </div>
          )}

          {/* User Management View */}
          {viewMode === 'users' && !selectedUser && (
            <div>
              <h2 className="text-xl font-semibold mb-4">User Management</h2>
              <p className="text-slate-400">Select a user from the sidebar to view details</p>
            </div>
          )}
        </main>
      </div>

      {/* Audit Logs Modal */}
      {showAuditModal && selectedUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold">Audit Trail - {selectedUser.name}</h2>
              <button
                onClick={() => setShowAuditModal(false)}
                className="text-slate-400 hover:text-white"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {auditLogs.length === 0 ? (
                <p className="text-slate-400">No audit logs available</p>
              ) : (
                auditLogs.map((log, i) => (
                  <div key={i} className="bg-slate-900 rounded-lg p-4 border border-slate-700">
                    <div className="flex justify-between items-start mb-2">
                      <div className="font-semibold text-blue-400">{log.log_type}</div>
                      <div className="text-sm text-slate-400">
                        {new Date(log.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="text-slate-300 mb-2">{log.description}</div>
                    {log.details && (
                      <div className="mt-2 p-3 bg-slate-800 rounded border border-slate-700">
                        {log.log_type === 'Circular Flow' && log.details.path && (
                          <div>
                            <div className="text-sm font-semibold text-slate-400 mb-1">Transaction Path:</div>
                            <div className="text-sm font-mono">
                              {log.details.path.join(' → ')}
                            </div>
                          </div>
                        )}
                        {log.log_type === 'Structuring' && log.details.transactions && (
                          <div>
                            <div className="text-sm font-semibold text-slate-400 mb-1">Suspicious Transactions:</div>
                            {log.details.transactions.map((tx: any, idx: number) => (
                              <div key={idx} className="text-sm mb-1">
                                ${tx.amount.toLocaleString()} at {new Date(tx.timestamp).toLocaleTimeString()}
                              </div>
                            ))}
                          </div>
                        )}
                        {log.details.ai_risk_score && (
                          <div className="text-sm mt-2">
                            <span className="text-slate-400">AI Risk Score: </span>
                            <span className="font-semibold">{(log.details.ai_risk_score * 100).toFixed(0)}%</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
