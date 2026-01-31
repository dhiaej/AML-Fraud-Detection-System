import { useState, useEffect } from 'react';
import axios from 'axios';

interface SubgraphNode {
  user_id: string;
  name: string;
  risk_score: number;
  predicted_risk_score?: number;
}

interface SubgraphLink {
  source: string;
  target: string;
  amount: number;
}

interface Subgraph {
  nodes: SubgraphNode[];
  links: SubgraphLink[];
}

interface FraudDetectionResult {
  riskScore: number | null;
  subgraph: Subgraph | null;
  loading: boolean;
  error: string | null;
  detectFraud: (userId: string) => Promise<void>;
}

const useFraudDetection = (): FraudDetectionResult => {
  const [riskScore, setRiskScore] = useState<number | null>(null);
  const [subgraph, setSubgraph] = useState<Subgraph | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const detectFraud = async (userId: string): Promise<void> => {
    if (!userId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`http://localhost:8000/api/v1/detect-fraud/${userId}`);
      setRiskScore(response.data.risk_probability);
      setSubgraph(response.data.subgraph);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to detect fraud');
      setRiskScore(null);
      setSubgraph(null);
    } finally {
      setLoading(false);
    }
  };

  return { riskScore, subgraph, loading, error, detectFraud };
};

export default useFraudDetection;
