import React from 'react';

const faces = ['front', 'back', 'right', 'left', 'top', 'bottom'];

export default function GiftBackground() {
  return <div className="page-backdrop" aria-hidden="true">
    <div className="ambient ambient-violet" />
    <div className="ambient ambient-rose" />
    <div className="background-grid" />
    <div className="gift-scene">
      <div className="scene-ring ring-one" />
      <div className="scene-ring ring-two" />
      <div className="gift-ground-shadow" />
      <div className="gift-float">
        <div className="gift-turntable">
          <div className="gift-body">
            {faces.map(face => <div key={face} className={`cube-face face-${face}`} />)}
          </div>
          <div className="gift-lid-3d">
            {faces.map(face => <div key={face} className={`lid-face lid-${face}`} />)}
          </div>
          <div className="gift-bow-3d bow-loop-one" />
          <div className="gift-bow-3d bow-loop-two" />
          <div className="bow-knot" />
        </div>
      </div>
      <span className="floating-star star-one">✦</span>
      <span className="floating-star star-two">✧</span>
      <span className="floating-star star-three">✦</span>
    </div>
  </div>;
}
