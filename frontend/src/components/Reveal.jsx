import React from 'react';
import { motion } from 'framer-motion';

export const Reveal = ({ children, delay = 0, y = 28, className = '', ...rest }) => (
  <motion.div
    className={className}
    initial={{ opacity: 0, y }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true, margin: '-80px' }}
    transition={{ duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] }}
    {...rest}
  >
    {children}
  </motion.div>
);

export const RevealStagger = ({ children, className = '', stagger = 0.1 }) => (
  <motion.div
    className={className}
    initial="hidden"
    whileInView="show"
    viewport={{ once: true, margin: '-80px' }}
    variants={{ hidden: {}, show: { transition: { staggerChildren: stagger } } }}
  >
    {children}
  </motion.div>
);

export const RevealItem = ({ children, className = '', y = 24 }) => (
  <motion.div
    className={className}
    variants={{
      hidden: { opacity: 0, y },
      show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] } },
    }}
  >
    {children}
  </motion.div>
);
