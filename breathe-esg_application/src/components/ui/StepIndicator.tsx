import React from 'react'

interface StepIndicatorProps {
  steps: string[]
  currentStep: number
  status: 'running' | 'done' | 'failed'
}

export function StepIndicator({ steps, currentStep, status }: StepIndicatorProps) {
  return (
    <div className="flex items-center gap-0">
      {steps.map((step, i) => {
        const isCompleted = i < currentStep
        const isActive = i === currentStep
        const isFailed = isActive && status === 'failed'

        let circleClass = 'bg-[#D1D5DB]' // pending
        if (isFailed) circleClass = 'bg-[#DC2626]'
        else if (isCompleted || (isActive && status === 'done')) circleClass = 'bg-[#16A34A]'
        else if (isActive) circleClass = 'bg-[#16A34A]'

        return (
          <React.Fragment key={step}>
            <div className="flex flex-col items-center gap-1.5">
              <div className={`relative h-8 w-8 rounded-full flex items-center justify-center ${circleClass}`}>
                {isActive && status === 'running' && (
                  <span className="absolute inset-0 rounded-full bg-[#16A34A] animate-ping opacity-40" />
                )}
                {isFailed ? (
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                ) : isCompleted || (isActive && status === 'done') ? (
                  <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <span className="h-2.5 w-2.5 rounded-full bg-white opacity-90" />
                )}
              </div>
              <span className={`text-xs font-medium ${isActive ? 'text-[#374151]' : 'text-[#9CA3AF]'}`}>
                {step}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`flex-1 h-0.5 mb-5 mx-1 ${isCompleted ? 'bg-[#16A34A]' : 'bg-[#E5E7EB]'}`} />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}
