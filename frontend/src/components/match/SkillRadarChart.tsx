import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
import { Radar } from 'react-chartjs-2';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface SkillRadarChartProps {
  skills: string[];
  candidateScores: number[];
  jobScores: number[];
}

export default function SkillRadarChart({ skills, candidateScores, jobScores }: SkillRadarChartProps) {
  const data = {
    labels: skills,
    datasets: [
      {
        label: 'Candidate',
        data: candidateScores,
        backgroundColor: 'rgba(99, 102, 241, 0.4)', // Indigo
        borderColor: 'rgba(99, 102, 241, 1)',
        borderWidth: 2,
        pointBackgroundColor: 'rgba(99, 102, 241, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(99, 102, 241, 1)',
      },
      {
        label: 'Job Requirement',
        data: jobScores,
        backgroundColor: 'rgba(16, 185, 129, 0.2)', // Emerald
        borderColor: 'rgba(16, 185, 129, 0.8)',
        borderWidth: 2,
        borderDash: [5, 5],
        pointBackgroundColor: 'rgba(16, 185, 129, 1)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgba(16, 185, 129, 1)',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      r: {
        angleLines: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        grid: {
          color: 'rgba(255, 255, 255, 0.1)',
        },
        pointLabels: {
          color: 'rgba(255, 255, 255, 0.7)',
          font: {
            size: 11,
            family: "'Inter', sans-serif"
          }
        },
        ticks: {
          display: false, // hide numbers on the axes
          min: 0,
          max: 100,
          stepSize: 20
        }
      },
    },
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: 'rgba(255, 255, 255, 0.7)',
          usePointStyle: true,
          boxWidth: 8,
          font: {
            family: "'Inter', sans-serif",
            size: 12
          }
        }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 21, 37, 0.9)',
        titleColor: '#fff',
        bodyColor: '#cbd5e1',
        borderColor: 'rgba(99, 102, 241, 0.3)',
        borderWidth: 1,
        padding: 10,
        cornerRadius: 8,
        displayColors: true,
      }
    },
  };

  return (
    <div className="w-full h-full min-h-[250px] flex items-center justify-center p-2">
      <Radar data={data} options={options} />
    </div>
  );
}
