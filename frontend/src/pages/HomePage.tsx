import React from 'react';
import { RegionalKitchens } from '../components/RegionalKitchens';
import { ArticlesSection, FaqSection, HomeHero, HowItWorksSection, ScienceBand } from '../components/HomeSections';

/** The landing page. Analysing a report happens on its own page (/analyze). */
export const HomePage: React.FC = () => (
  <div className="-mb-10 flow-root space-y-16 sm:-mb-14 sm:space-y-20">
    <HomeHero />
    <RegionalKitchens />
    <HowItWorksSection />
    <ScienceBand />
    <ArticlesSection />
    <FaqSection />
  </div>
);
