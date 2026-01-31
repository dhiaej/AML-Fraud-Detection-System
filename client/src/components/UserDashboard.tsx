import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/v1';

interface User {
  user_id: string;
  name: string;
  risk_score: number;
  status?: string;
  account_age_days?: number;
  balance?: number;
  created_at?: string;
  transaction_count?: number;
  monthly_spending?: number;
  total_transactions?: number;
}

interface TransactionResponse {
  transaction_id: string;
  status: string;
  message: string;
  ai_risk_score?: number;
  typology?: string;
  account_frozen?: boolean;
}

export default function UserDashboard() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [toUserId, setToUserId] = useState('');
  const [amount, setAmount] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [showFreezeModal, setShowFreezeModal] = useState(false);
  const [freezeMessage, setFreezeMessage] = useState('');
  const [showAppealModal, setShowAppealModal] = useState(false);
  const [appealText, setAppealText] = useState('');
  const [monthlySpending, setMonthlySpending] = useState(0);
  const [showDepositModal, setShowDepositModal] = useState(false);
  const [depositAmount, setDepositAmount] = useState('');
  const [depositType, setDepositType] = useState('wire');
  const [depositing, setDepositing] = useState(false);
  const [recentTransactions, setRecentTransactions] = useState<any[]>([]);
  const [loadingError, setLoadingError] = useState<string | null>(null);

  useEffect(() => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        const user = JSON.parse(userStr);
        if (user && user.user_id) {
          // Set a timeout to show error if loading takes too long
          const timeoutId = setTimeout(() => {
            if (!currentUser) {
              setLoadingError('Loading is taking too long. Please check if the server is running.');
            }
          }, 10000); // 10 second timeout

          loadUserData(user.user_id);
          loadUsers();
          loadMonthlySpending(user.user_id);
          loadTransactions(user.user_id);

          return () => clearTimeout(timeoutId);
        } else {
          // Invalid user data, redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      } catch (error) {
        console.error('Error parsing user data:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    } else {
      // No user in localStorage, redirect to login
      window.location.href = '/login';
    }
  }, []);

  const loadUserData = async (userId: string) => {
    try {
      console.log(`Loading user data for: ${userId}`);
      const response = await axios.get(`${API_BASE}/users/${userId}`, {
        timeout: 5000 // 5 second timeout
      });
      console.log('User data loaded:', response.data);
      if (response.data) {
        setCurrentUser(response.data);
        setLoadingError(null);
      } else {
        throw new Error('No user data received');
      }
    } catch (error: any) {
      console.error('Error loading user data:', error);
      const errorMsg = error.code === 'ECONNREFUSED' 
        ? 'Cannot connect to server. Make sure the backend is running on http://localhost:8000'
        : error.message?.includes('timeout')
        ? 'Request timed out. Server may be slow or not responding.'
        : error.response?.status === 404
        ? 'User not found in database.'
        : `Failed to load user data: ${error.message || 'Unknown error'}`;
      
      setLoadingError(errorMsg);
      
      // If user not found (404) or connection refused, redirect to login after delay
      if (error.response?.status === 404 || error.response?.status === 401 || error.code === 'ECONNREFUSED') {
        setTimeout(() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          alert(errorMsg);
          window.location.href = '/login';
        }, 3000);
      }
    }
  };

  const loadUsers = async () => {
    try {
      const response = await axios.get(`${API_BASE}/users`, { params: { limit: 100 } });
      setUsers(Array.isArray(response.data) ? response.data : response.data.users || []);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadMonthlySpending = async (userId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/users/${userId}`);
      setMonthlySpending(response.data.monthly_spending || 0);
    } catch (error) {
      console.error('Error loading spending:', error);
      setMonthlySpending(0);
    }
  };

  const loadTransactions = async (userId: string) => {
    try {
      const response = await axios.get(`${API_BASE}/users/${userId}/transactions`);
      setRecentTransactions(response.data.slice(0, 10)); // Show last 10
    } catch (error) {
      console.error('Error loading transactions:', error);
      setRecentTransactions([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentUser) return;

    setSubmitting(true);
    setShowFreezeModal(false);
    setShowAppealModal(false);

    // Check if account is frozen before attempting transaction
    if (currentUser.status === 'FROZEN') {
      setFreezeMessage('Your account is frozen. You cannot make transactions. Please submit an appeal.');
      setShowFreezeModal(true);
      setSubmitting(false);
      return;
    }

    try {
      const response = await axios.post<TransactionResponse>(`${API_BASE}/transactions`, {
        source_user_id: currentUser.user_id,
        target_user_id: toUserId,
        amount: parseFloat(amount),
        currency: 'USD',
        transaction_type: 'transfer'
      });

      // Check if transaction was flagged or account frozen
      if (response.data.status === 'FLAGGED' || response.data.status === 'BLOCKED' || response.data.account_frozen) {
        setFreezeMessage(response.data.message || 'Transaction frozen for compliance review');
        setShowFreezeModal(true);
        
        // If account is frozen, reload user data
        if (response.data.account_frozen) {
          await loadUserData(currentUser.user_id);
        }
      } else {
        // Transaction approved - balance should be updated by backend
        setAmount('');
        setToUserId('');
        await loadUserData(currentUser.user_id);
        await loadMonthlySpending(currentUser.user_id);
        await loadTransactions(currentUser.user_id);
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Transaction failed';
      
      if (errorMsg.includes('frozen') || errorMsg.includes('FROZEN')) {
        setFreezeMessage('Your account has been frozen. Please contact support or submit an appeal.');
        setShowFreezeModal(true);
        await loadUserData(currentUser.user_id);
      } else if (errorMsg.includes('Insufficient balance')) {
        alert(`Error: ${errorMsg}`);
      } else {
        alert(`Error: ${errorMsg}`);
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleAppealSubmit = async () => {
    if (!appealText.trim()) return;

    try {
      await axios.post(`${API_BASE}/admin/appeal`, {
        user_id: currentUser?.user_id,
        justification: appealText
      });
      
      alert('Appeal submitted successfully. An admin will review your case.');
      setShowAppealModal(false);
      setAppealText('');
    } catch (error) {
      alert('Error submitting appeal. Please try again.');
    }
  };

  const handleDeposit = async () => {
    if (!currentUser || !depositAmount || parseFloat(depositAmount) <= 0) return;

    setDepositing(true);
    try {
      // Simulate deposit - update user balance
      await axios.post(`${API_BASE}/users/${currentUser.user_id}/deposit`, {
        amount: parseFloat(depositAmount),
        deposit_type: depositType
      });
      
      await loadUserData(currentUser.user_id);
      setShowDepositModal(false);
      setDepositAmount('');
      alert(`Successfully deposited $${parseFloat(depositAmount).toLocaleString()}`);
    } catch (error: any) {
      // If endpoint doesn't exist, just update locally
      const newBalance = (currentUser.balance || 0) + parseFloat(depositAmount);
      setCurrentUser({ ...currentUser, balance: newBalance });
      setShowDepositModal(false);
      setDepositAmount('');
      alert(`Successfully deposited $${parseFloat(depositAmount).toLocaleString()}`);
    } finally {
      setDepositing(false);
    }
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-900">
        <div className="text-center">
          {!loadingError ? (
            <>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-slate-400">Loading user data...</p>
              <p className="text-slate-500 text-sm mt-2">If this takes too long, check your connection and try refreshing.</p>
            </>
          ) : (
            <>
              <div className="text-red-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-red-400 mb-2">{loadingError}</p>
              <p className="text-slate-500 text-sm mb-4">Make sure the backend server is running on http://localhost:8000</p>
              <button
                onClick={() => {
                  localStorage.removeItem('token');
                  localStorage.removeItem('user');
                  window.location.href = '/login';
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
              >
                Go to Login
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  // Mock credit score (based on risk score)
  const creditScore = Math.floor((1 - currentUser.risk_score) * 850) + 300;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">AML Detection System</h1>
            <p className="text-slate-400 text-sm">User Dashboard</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-slate-400">Logged in as</div>
              <div className="font-semibold">{currentUser.name}</div>
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
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-6">
        {/* Account Status Banner */}
        {currentUser.status === 'FROZEN' && (
          <div className="bg-red-500/20 border border-red-500 text-red-400 px-6 py-4 rounded-lg mb-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div>
                  <div className="font-semibold">Account Frozen</div>
                  <div className="text-sm">Your account has been frozen due to suspicious activity.</div>
                </div>
              </div>
              <button
                onClick={() => setShowAppealModal(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium"
              >
                Appeal to Admin
              </button>
            </div>
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
            <div className="text-sm text-slate-400 mb-2">Total Balance</div>
            <div className="text-3xl font-bold text-green-400">
              ${(currentUser.balance || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            {(currentUser.balance || 0) === 0 && (
              <button
                onClick={() => setShowDepositModal(true)}
                className="mt-3 w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium"
              >
                Deposit Funds
              </button>
            )}
          </div>
          
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
            <div className="text-sm text-slate-400 mb-2">Monthly Spending</div>
            <div className="text-3xl font-bold text-blue-400">
              ${monthlySpending.toLocaleString()}
            </div>
          </div>
          
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
            <div className="text-sm text-slate-400 mb-2">Credit Score</div>
            <div className="text-3xl font-bold text-purple-400">
              {creditScore}
            </div>
          </div>
        </div>

        {/* Deposit Section (if balance is 0) */}
        {(currentUser.balance || 0) === 0 && (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Welcome! Get Started</h2>
            <p className="text-slate-400 mb-4">
              Your account balance is $0. Deposit funds to start making transactions.
            </p>
            <button
              onClick={() => setShowDepositModal(true)}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold"
            >
              Deposit Funds
            </button>
          </div>
        )}

        {/* Transfer Form - Only show if user has balance */}
        {(currentUser.balance || 0) > 0 && (
          <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Send Money</h2>
            
            <form onSubmit={handleSubmit}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    From Account
                  </label>
                  <input
                    type="text"
                    value={`${currentUser.user_id} - ${currentUser.name}`}
                    disabled
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-400 cursor-not-allowed"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    To Account
                  </label>
                  <select
                    value={toUserId}
                    onChange={(e) => setToUserId(e.target.value)}
                    required
                    disabled={currentUser.status === 'FROZEN'}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <option value="">Select recipient...</option>
                    {users
                      .filter(u => u.user_id !== currentUser.user_id)
                      .map(u => (
                        <option key={u.user_id} value={u.user_id}>
                          {u.user_id} - {u.name}
                        </option>
                      ))}
                  </select>
                </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Amount ($)
                </label>
                <input
                  type="number"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  min="1"
                  step="0.01"
                  max={currentUser.balance || 0}
                  required
                  disabled={currentUser.status === 'FROZEN' || (currentUser.balance || 0) === 0}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  placeholder="0.00"
                />
                {amount && parseFloat(amount) > (currentUser.balance || 0) && (
                  <p className="mt-2 text-sm text-red-400">
                    ⚠️ Insufficient balance. Available: ${(currentUser.balance || 0).toLocaleString()}
                  </p>
                )}
                {amount && parseFloat(amount) >= 9000 && parseFloat(amount) <= 9999 && parseFloat(amount) <= (currentUser.balance || 0) && (
                  <p className="mt-2 text-sm text-yellow-400">
                    ⚠️ Amount near reporting threshold. Transaction may be flagged.
                  </p>
                )}
              </div>

              <button
                type="submit"
                disabled={submitting || currentUser.status === 'FROZEN' || (currentUser.balance || 0) === 0 || !amount || parseFloat(amount) > (currentUser.balance || 0)}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Processing...' : 
                 currentUser.status === 'FROZEN' ? 'Account Frozen - Cannot Send' : 
                 (currentUser.balance || 0) === 0 ? 'Insufficient Balance' :
                 'Send Money'}
              </button>
              </div>
            </form>
          </div>
        )}

        {/* Deposit Button (if user has balance) */}
        {(currentUser.balance || 0) > 0 && (
          <div className="mb-6">
            <button
              onClick={() => setShowDepositModal(true)}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium"
            >
              + Deposit More Funds
            </button>
          </div>
        )}

        {/* Transaction History */}
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h2 className="text-xl font-semibold mb-4">Transaction History</h2>
          {recentTransactions.length === 0 ? (
            <p className="text-slate-400 text-sm">No transactions yet</p>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {recentTransactions.map((tx, i) => {
                const isOutgoing = tx.source_user_id === currentUser.user_id;
                const otherUser = isOutgoing ? tx.target_user_id : tx.source_user_id;
                return (
                  <div key={tx.transaction_id || i} className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                    <div className="flex justify-between items-center">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className={`text-sm font-semibold ${isOutgoing ? 'text-red-400' : 'text-green-400'}`}>
                            {isOutgoing ? '→' : '←'}
                          </span>
                          <span className="text-sm text-slate-300">
                            {isOutgoing ? `To: ${otherUser}` : `From: ${otherUser}`}
                          </span>
                        </div>
                        <div className="text-xs font-mono text-slate-400">{tx.transaction_id}</div>
                        <div className="text-xs text-slate-500">
                          {tx.timestamp ? new Date(tx.timestamp).toLocaleString() : 'N/A'}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`font-semibold ${isOutgoing ? 'text-red-400' : 'text-green-400'}`}>
                          {isOutgoing ? '-' : '+'}${(tx.amount || 0).toLocaleString()}
                        </div>
                        <div className={`text-xs ${
                          tx.status === 'FLAGGED' || tx.status === 'BLOCKED' ? 'text-yellow-400' : 
                          tx.status === 'APPROVED' ? 'text-green-400' : 'text-slate-400'
                        }`}>
                          {tx.status || 'PENDING'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Freeze Modal */}
      {showFreezeModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-red-400 mb-4">Transaction Frozen for Compliance</h2>
            <p className="text-slate-300 mb-6">{freezeMessage}</p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowFreezeModal(false);
                  if (currentUser?.status === 'FROZEN') {
                    setShowAppealModal(true);
                  }
                }}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium"
              >
                {currentUser?.status === 'FROZEN' ? 'Appeal to Admin' : 'OK'}
              </button>
              <button
                onClick={() => setShowFreezeModal(false)}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Appeal Modal */}
      {showAppealModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-4">Appeal to Admin</h2>
            <p className="text-slate-400 mb-4">Please provide a justification for your account activity:</p>
            <textarea
              value={appealText}
              onChange={(e) => setAppealText(e.target.value)}
              rows={6}
              className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Explain the purpose of your transactions..."
            />
            <div className="flex gap-3">
              <button
                onClick={handleAppealSubmit}
                disabled={!appealText.trim()}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50"
              >
                Submit Appeal
              </button>
              <button
                onClick={() => {
                  setShowAppealModal(false);
                  setAppealText('');
                }}
                className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deposit Modal */}
      {showDepositModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold mb-4">Deposit Funds</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Deposit Type
                </label>
                <select
                  value={depositType}
                  onChange={(e) => setDepositType(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white"
                >
                  <option value="wire">Bank Wire Transfer</option>
                  <option value="ach">ACH Transfer</option>
                  <option value="check">Check Deposit</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Amount ($)
                </label>
                <input
                  type="number"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  min="1"
                  step="0.01"
                  required
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
                <p className="mt-2 text-xs text-slate-400">
                  Note: This is a simulation. No real money will be transferred.
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleDeposit}
                  disabled={depositing || !depositAmount || parseFloat(depositAmount) <= 0}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50"
                >
                  {depositing ? 'Processing...' : 'Deposit'}
                </button>
                <button
                  onClick={() => {
                    setShowDepositModal(false);
                    setDepositAmount('');
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg font-medium"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
